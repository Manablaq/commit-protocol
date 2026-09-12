from __future__ import annotations

import json
import math
from typing import Any


POSTGRES_DRIVER_SCHEMA = (
    "commit-neon-postgres-driver-v1"
)

PHYSICAL_STORAGE_PROVIDER = (
    "NEON_POSTGRES"
)

DATABASE_ENGINE = (
    "POSTGRESQL"
)

DATABASE_DRIVER = (
    "PSYCOPG_3"
)

POSTGRES_TABLE = (
    "commit_backend_state"
)

POSTGRES_BIGINT_MAX = (
    2**63
    - 1
)


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS commit_backend_state (
    namespace TEXT PRIMARY KEY,
    revision BIGINT NOT NULL CHECK (revision > 0),
    payload BYTEA NOT NULL
)
""".strip()


_READ_SQL = """
SELECT revision, payload
FROM commit_backend_state
WHERE namespace = %s
""".strip()


_INITIAL_CAS_SQL = """
INSERT INTO commit_backend_state (
    namespace,
    revision,
    payload
)
VALUES (%s, %s, %s)
ON CONFLICT (namespace) DO NOTHING
RETURNING revision
""".strip()


_UPDATE_CAS_SQL = """
UPDATE commit_backend_state
SET
    revision = %s,
    payload = %s
WHERE
    namespace = %s
    AND revision = %s
RETURNING revision
""".strip()


class PostgresDriverError(
    RuntimeError
):
    """Base error for the physical PostgreSQL storage driver."""


class PostgresDriverCorruptionError(
    PostgresDriverError
):
    """Raised when database state contradicts the canonical snapshot."""


def _require_database_url(
    value: object,
) -> str:
    if (
        type(value) is not str
        or value == ""
        or "\x00" in value
    ):
        raise PostgresDriverError(
            "database_url must be a nonempty string"
        )

    return value


def _require_namespace(
    value: object,
) -> str:
    if (
        type(value) is not str
        or value == ""
        or "\x00" in value
    ):
        raise PostgresDriverError(
            "namespace must be a nonempty NUL-free string"
        )

    return value


def _require_revision(
    value: object,
    *,
    label: str,
) -> int:
    if (
        type(value) is not int
        or value < 0
        or value
        >= POSTGRES_BIGINT_MAX
    ):
        raise PostgresDriverError(
            label
            + " must be an integer in PostgreSQL CAS range 0..2^63-2"
        )

    return value


def _reject_duplicate_keys(
    pairs: list[
        tuple[
            str,
            Any,
        ]
    ],
) -> dict[str, Any]:
    result: dict[
        str,
        Any,
    ] = {}

    for key, value in pairs:
        if key in result:
            raise PostgresDriverError(
                "snapshot contains duplicate JSON object keys"
            )

        result[
            key
        ] = value

    return result


def _reject_nonfinite(
    value: str,
) -> None:
    raise PostgresDriverError(
        "snapshot contains non-finite JSON number "
        + value
    )


def _validate_strict_json(
    value: object,
) -> None:
    value_type = type(
        value
    )

    if (
        value is None
        or value_type is bool
        or value_type is int
        or value_type is str
    ):
        return

    if value_type is float:
        if not math.isfinite(
            value
        ):
            raise PostgresDriverError(
                "snapshot contains non-finite number"
            )

        return

    if value_type is list:
        for child in value:
            _validate_strict_json(
                child
            )

        return

    if value_type is dict:
        for key, child in value.items():
            if type(
                key
            ) is not str:
                raise PostgresDriverError(
                    "snapshot contains non-string JSON object key"
                )

            _validate_strict_json(
                child
            )

        return

    raise PostgresDriverError(
        "snapshot contains non-JSON value"
    )


def _payload_bytes(
    value: object,
    *,
    corruption: bool,
) -> bytes:
    error_type = (
        PostgresDriverCorruptionError
        if corruption
        else PostgresDriverError
    )

    if isinstance(
        value,
        memoryview,
    ):
        raw = value.tobytes()
    elif type(
        value
    ) is bytearray:
        raw = bytes(
            value
        )
    elif type(
        value
    ) is bytes:
        raw = bytes(
            bytearray(
                value
            )
        )
    else:
        raise error_type(
            "snapshot payload must be bytes"
        )

    return raw


def _decode_canonical_snapshot(
    payload: object,
    *,
    corruption: bool,
) -> tuple[
    bytes,
    int,
]:
    error_type = (
        PostgresDriverCorruptionError
        if corruption
        else PostgresDriverError
    )

    raw = _payload_bytes(
        payload,
        corruption=corruption,
    )

    try:
        text = raw.decode(
            "utf-8"
        )
    except UnicodeError as exc:
        raise error_type(
            "snapshot payload is not valid UTF-8"
        ) from exc

    try:
        decoded = json.loads(
            text,
            object_pairs_hook=(
                _reject_duplicate_keys
            ),
            parse_constant=(
                _reject_nonfinite
            ),
        )
    except PostgresDriverError as exc:
        raise error_type(
            "snapshot payload is not canonical JSON"
        ) from exc
    except (
        json.JSONDecodeError,
        TypeError,
        ValueError,
    ) as exc:
        raise error_type(
            "snapshot payload is not valid JSON"
        ) from exc

    if type(
        decoded
    ) is not dict:
        raise error_type(
            "snapshot payload must decode to an object"
        )

    try:
        _validate_strict_json(
            decoded
        )

        canonical = json.dumps(
            decoded,
            sort_keys=True,
            separators=(
                ",",
                ":",
            ),
            ensure_ascii=False,
            allow_nan=False,
        ).encode(
            "utf-8"
        )
    except PostgresDriverError as exc:
        raise error_type(
            "snapshot payload is not canonical JSON"
        ) from exc
    except (
        TypeError,
        ValueError,
        UnicodeError,
    ) as exc:
        raise error_type(
            "snapshot payload cannot be canonicalized"
        ) from exc

    if canonical != raw:
        raise error_type(
            "snapshot payload bytes are not canonical"
        )

    revision = decoded.get(
        "revision"
    )

    if (
        type(
            revision
        ) is not int
        or revision <= 0
        or revision
        > POSTGRES_BIGINT_MAX
    ):
        raise error_type(
            "snapshot revision must be in PostgreSQL BIGINT range 1..2^63-1"
        )

    return (
        raw,
        revision,
    )


def _require_result_revision(
    row: object,
    *,
    expected_revision: int,
) -> None:
    if (
        type(row) not in (
            tuple,
            list,
        )
        or len(
            row
        )
        != 1
    ):
        raise PostgresDriverCorruptionError(
            "PostgreSQL CAS returned malformed row"
        )

    revision = row[
        0
    ]

    if (
        type(
            revision
        )
        is not int
        or revision
        != expected_revision
    ):
        raise PostgresDriverCorruptionError(
            "PostgreSQL CAS returned unexpected revision"
        )


class PostgresAtomicDriver:
    def __init__(
        self,
        *,
        database_url,
        connect,
    ):
        self._database_url = (
            _require_database_url(
                database_url
            )
        )

        if not callable(
            connect
        ):
            raise PostgresDriverError(
                "connect must be callable"
            )

        self._connect = connect

    def _open_connection(
        self,
    ):
        try:
            return self._connect(
                self._database_url,
                autocommit=True,
            )
        except Exception as exc:
            raise PostgresDriverError(
                "PostgreSQL connection failed"
            ) from exc

    def read(
        self,
        *,
        namespace,
    ):
        checked_namespace = (
            _require_namespace(
                namespace
            )
        )

        try:
            connection = (
                self._open_connection()
            )

            with connection as active:
                result = active.execute(
                    _READ_SQL,
                    (
                        checked_namespace,
                    ),
                )

                row = result.fetchone()

        except PostgresDriverError:
            raise
        except Exception as exc:
            raise PostgresDriverError(
                "PostgreSQL read failed"
            ) from exc

        if row is None:
            return None

        if (
            type(
                row
            )
            not in (
                tuple,
                list,
            )
            or len(
                row
            )
            != 2
        ):
            raise PostgresDriverCorruptionError(
                "PostgreSQL read returned malformed row"
            )

        database_revision = row[
            0
        ]

        if (
            type(
                database_revision
            )
            is not int
            or database_revision <= 0
            or database_revision
            > POSTGRES_BIGINT_MAX
        ):
            raise PostgresDriverCorruptionError(
                "PostgreSQL row contains revision outside BIGINT domain"
            )

        payload, payload_revision = (
            _decode_canonical_snapshot(
                row[
                    1
                ],
                corruption=True,
            )
        )

        if (
            database_revision
            != payload_revision
        ):
            raise PostgresDriverCorruptionError(
                "database revision does not match snapshot revision"
            )

        return bytes(
            bytearray(
                payload
            )
        )

    def compare_and_swap(
        self,
        *,
        namespace,
        expected_revision,
        payload,
    ) -> bool:
        checked_namespace = (
            _require_namespace(
                namespace
            )
        )

        checked_revision = (
            _require_revision(
                expected_revision,
                label=(
                    "expected_revision"
                ),
            )
        )

        canonical_payload, payload_revision = (
            _decode_canonical_snapshot(
                payload,
                corruption=False,
            )
        )

        next_revision = (
            checked_revision
            + 1
        )

        if (
            payload_revision
            != next_revision
        ):
            raise PostgresDriverError(
                "snapshot revision does not equal expected_revision + 1"
            )

        if checked_revision == 0:
            statement = (
                _INITIAL_CAS_SQL
            )

            parameters = (
                checked_namespace,
                next_revision,
                canonical_payload,
            )
        else:
            statement = (
                _UPDATE_CAS_SQL
            )

            parameters = (
                next_revision,
                canonical_payload,
                checked_namespace,
                checked_revision,
            )

        try:
            connection = (
                self._open_connection()
            )

            with connection as active:
                result = active.execute(
                    statement,
                    parameters,
                )

                row = result.fetchone()

        except PostgresDriverError:
            raise
        except Exception as exc:
            raise PostgresDriverError(
                "PostgreSQL compare-and-swap failed"
            ) from exc

        if row is None:
            return False

        _require_result_revision(
            row,
            expected_revision=(
                next_revision
            ),
        )

        return True
