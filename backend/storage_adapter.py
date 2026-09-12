from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import math
import re
from typing import Any

from backend.persistence import (
    PersistenceError,
    apply_index_observation,
    apply_transaction_observation,
    empty_persistence_state,
    validate_persistence_state,
)


STORAGE_SNAPSHOT_SCHEMA = (
    "commit-backend-storage-snapshot-v1"
)

STORAGE_DRIVER_PROTOCOL = (
    "ATOMIC_COMPARE_AND_SWAP_V1"
)

INITIAL_STORAGE_REVISION = 0


_DIGEST_PATTERN = re.compile(
    r"^[0-9a-f]{64}$"
)

_SNAPSHOT_FIELDS = {
    "schema",
    "revision",
    "state_digest",
    "state",
}


class StorageAdapterError(
    ValueError
):
    """Base error for durable-state adapter failures."""


class StorageConflictError(
    StorageAdapterError
):
    """Raised when optimistic compare-and-swap fails."""


class StorageCorruptionError(
    StorageAdapterError
):
    """Raised when stored bytes are malformed or inconsistent."""


def _require_namespace(
    value: object,
) -> str:
    if (
        type(value) is not str
        or value == ""
    ):
        raise StorageAdapterError(
            "namespace must be a nonempty string"
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
    ):
        raise StorageAdapterError(
            label
            + " must be a nonnegative integer"
        )

    return value


def _validate_strict_json_value(
    value: object,
    *,
    value_path: str = "$",
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
            raise StorageAdapterError(
                value_path
                + " contains a non-finite number"
            )

        return

    if value_type is list:
        for index, child in enumerate(
            value
        ):
            _validate_strict_json_value(
                child,
                value_path=(
                    value_path
                    + "["
                    + str(
                        index
                    )
                    + "]"
                ),
            )

        return

    if value_type is dict:
        for key, child in value.items():
            if type(
                key
            ) is not str:
                raise StorageAdapterError(
                    value_path
                    + " contains a non-string object key"
                )

            _validate_strict_json_value(
                child,
                value_path=(
                    value_path
                    + "."
                    + key
                ),
            )

        return

    raise StorageAdapterError(
        value_path
        + " contains a non-JSON value"
    )


def _canonical_bytes(
    value: object,
) -> bytes:
    _validate_strict_json_value(
        value
    )

    try:
        return json.dumps(
            value,
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
    except (
        TypeError,
        ValueError,
        UnicodeError,
    ) as exc:
        raise StorageAdapterError(
            "value is not canonical-JSON serializable"
        ) from exc


def _canonical_digest(
    value: object,
) -> str:
    return hashlib.sha256(
        _canonical_bytes(
            value
        )
    ).hexdigest()


def _validated_state(
    state: object,
) -> dict[str, Any]:
    try:
        validated = (
            validate_persistence_state(
                state
            )
        )
    except PersistenceError as exc:
        raise StorageAdapterError(
            "invalid persistence state"
        ) from exc

    return deepcopy(
        validated
    )


def _reject_duplicate_object_keys(
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
            raise StorageCorruptionError(
                "stored snapshot contains duplicate object keys"
            )

        result[
            key
        ] = value

    return result


def _reject_nonfinite_constant(
    value: str,
) -> None:
    raise StorageCorruptionError(
        "stored snapshot contains non-finite number "
        + value
    )


def _decode_snapshot_bytes(
    raw: object,
) -> dict[str, Any]:
    if type(
        raw
    ) is not bytes:
        raise StorageCorruptionError(
            "stored snapshot must be bytes"
        )

    try:
        text = raw.decode(
            "utf-8"
        )
    except UnicodeError as exc:
        raise StorageCorruptionError(
            "stored snapshot is not valid UTF-8"
        ) from exc

    try:
        decoded = json.loads(
            text,
            object_pairs_hook=(
                _reject_duplicate_object_keys
            ),
            parse_constant=(
                _reject_nonfinite_constant
            ),
        )
    except StorageCorruptionError:
        raise
    except (
        json.JSONDecodeError,
        TypeError,
        ValueError,
    ) as exc:
        raise StorageCorruptionError(
            "stored snapshot is not valid JSON"
        ) from exc

    if type(
        decoded
    ) is not dict:
        raise StorageCorruptionError(
            "stored snapshot must be an object"
        )

    return decoded


def _validate_snapshot(
    snapshot: object,
    *,
    require_stored_revision: bool,
) -> dict[str, Any]:
    if type(
        snapshot
    ) is not dict:
        raise StorageCorruptionError(
            "snapshot must be an object"
        )

    if set(
        snapshot
    ) != _SNAPSHOT_FIELDS:
        raise StorageCorruptionError(
            "snapshot fields do not match schema"
        )

    if (
        snapshot.get(
            "schema"
        )
        != STORAGE_SNAPSHOT_SCHEMA
    ):
        raise StorageCorruptionError(
            "invalid snapshot schema"
        )

    revision = snapshot.get(
        "revision"
    )

    if (
        type(
            revision
        )
        is not int
        or revision < 0
    ):
        raise StorageCorruptionError(
            "invalid snapshot revision"
        )

    if (
        require_stored_revision
        and revision
        <= INITIAL_STORAGE_REVISION
    ):
        raise StorageCorruptionError(
            "stored snapshot revision must be positive"
        )

    state_digest = snapshot.get(
        "state_digest"
    )

    if (
        type(
            state_digest
        )
        is not str
        or _DIGEST_PATTERN.fullmatch(
            state_digest
        )
        is None
    ):
        raise StorageCorruptionError(
            "invalid state digest"
        )

    try:
        state = (
            validate_persistence_state(
                snapshot.get(
                    "state"
                )
            )
        )
    except PersistenceError as exc:
        raise StorageCorruptionError(
            "stored persistence state is invalid"
        ) from exc

    expected_digest = (
        _canonical_digest(
            state
        )
    )

    if (
        state_digest
        != expected_digest
    ):
        raise StorageCorruptionError(
            "stored state digest mismatch"
        )

    return {
        "schema": (
            STORAGE_SNAPSHOT_SCHEMA
        ),
        "revision": revision,
        "state_digest": (
            state_digest
        ),
        "state": deepcopy(
            state
        ),
    }


def _missing_snapshot() -> dict[str, Any]:
    state = (
        empty_persistence_state()
    )

    validated_state = (
        _validated_state(
            state
        )
    )

    return {
        "schema": (
            STORAGE_SNAPSHOT_SCHEMA
        ),
        "revision": (
            INITIAL_STORAGE_REVISION
        ),
        "state_digest": (
            _canonical_digest(
                validated_state
            )
        ),
        "state": (
            validated_state
        ),
    }


def _validate_monotonic_transition(
    *,
    current_state: object,
    next_state: object,
) -> dict[str, Any]:
    current = _validated_state(
        current_state
    )

    target = _validated_state(
        next_state
    )

    working = deepcopy(
        current
    )

    try:
        for record_key in sorted(
            target[
                "index_records"
            ]
        ):
            target_record = target[
                "index_records"
            ][
                record_key
            ]

            current_record = working[
                "index_records"
            ].get(
                record_key
            )

            if (
                current_record
                == target_record
            ):
                continue

            working = (
                apply_index_observation(
                    state=working,
                    observation=(
                        target_record[
                            "payload"
                        ]
                    ),
                )
            )

        for record_key in sorted(
            target[
                "transaction_records"
            ]
        ):
            target_record = target[
                "transaction_records"
            ][
                record_key
            ]

            current_record = working[
                "transaction_records"
            ].get(
                record_key
            )

            if (
                current_record
                == target_record
            ):
                continue

            working = (
                apply_transaction_observation(
                    state=working,
                    observation=(
                        target_record[
                            "payload"
                        ]
                    ),
                )
            )

    except PersistenceError as exc:
        raise StorageAdapterError(
            "durable state transition violates persistence transition rules"
        ) from exc

    try:
        replayed = (
            validate_persistence_state(
                working
            )
        )
    except PersistenceError as exc:
        raise StorageAdapterError(
            "replayed durable state is invalid"
        ) from exc

    if replayed != target:
        raise StorageAdapterError(
            "durable state transition is not a monotonic persistence extension"
        )

    return deepcopy(
        target
    )


class DurableStateStore:
    def __init__(
        self,
        *,
        driver,
        namespace,
    ):
        self._namespace = (
            _require_namespace(
                namespace
            )
        )

        read = getattr(
            driver,
            "read",
            None,
        )

        compare_and_swap = getattr(
            driver,
            "compare_and_swap",
            None,
        )

        if not callable(
            read
        ):
            raise StorageAdapterError(
                "driver must provide read"
            )

        if not callable(
            compare_and_swap
        ):
            raise StorageAdapterError(
                "driver must provide compare_and_swap"
            )

        self._driver = driver

    def _read_raw(
        self,
    ):
        try:
            return self._driver.read(
                namespace=(
                    self._namespace
                )
            )
        except Exception as exc:
            raise StorageAdapterError(
                "storage driver read failed"
            ) from exc

    def _compare_and_swap(
        self,
        *,
        expected_revision: int,
        payload: bytes,
    ) -> bool:
        try:
            result = (
                self._driver.compare_and_swap(
                    namespace=(
                        self._namespace
                    ),
                    expected_revision=(
                        expected_revision
                    ),
                    payload=payload,
                )
            )
        except Exception as exc:
            raise StorageAdapterError(
                "storage driver write failed"
            ) from exc

        if type(
            result
        ) is not bool:
            raise StorageAdapterError(
                "storage driver compare_and_swap must return bool"
            )

        return result

    def load(
        self,
    ) -> dict[str, Any]:
        raw = self._read_raw()

        if raw is None:
            return deepcopy(
                _missing_snapshot()
            )

        snapshot = (
            _decode_snapshot_bytes(
                raw
            )
        )

        validated = (
            _validate_snapshot(
                snapshot,
                require_stored_revision=True,
            )
        )

        try:
            canonical = (
                _canonical_bytes(
                    validated
                )
            )
        except StorageAdapterError as exc:
            raise StorageCorruptionError(
                "stored snapshot cannot be canonicalized"
            ) from exc

        if raw != canonical:
            raise StorageCorruptionError(
                "stored snapshot bytes are not canonical"
            )

        return deepcopy(
            validated
        )

    def save(
        self,
        *,
        state,
        expected_revision,
    ) -> dict[str, Any]:
        checked_revision = (
            _require_revision(
                expected_revision,
                label=(
                    "expected_revision"
                ),
            )
        )

        validated_state = (
            _validated_state(
                state
            )
        )

        desired_digest = (
            _canonical_digest(
                validated_state
            )
        )

        current = self.load()

        if (
            current[
                "revision"
            ]
            != checked_revision
        ):
            raise StorageConflictError(
                "stale storage revision"
            )

        if (
            current[
                "state_digest"
            ]
            == desired_digest
            and current[
                "state"
            ]
            == validated_state
        ):
            return deepcopy(
                current
            )

        validated_state = (
            _validate_monotonic_transition(
                current_state=(
                    current[
                        "state"
                    ]
                ),
                next_state=(
                    validated_state
                ),
            )
        )

        desired_digest = (
            _canonical_digest(
                validated_state
            )
        )

        next_revision = (
            checked_revision
            + 1
        )

        snapshot = {
            "schema": (
                STORAGE_SNAPSHOT_SCHEMA
            ),
            "revision": (
                next_revision
            ),
            "state_digest": (
                desired_digest
            ),
            "state": deepcopy(
                validated_state
            ),
        }

        validated_snapshot = (
            _validate_snapshot(
                snapshot,
                require_stored_revision=True,
            )
        )

        payload = (
            _canonical_bytes(
                validated_snapshot
            )
        )

        committed = (
            self._compare_and_swap(
                expected_revision=(
                    checked_revision
                ),
                payload=payload,
            )
        )

        if not committed:
            raise StorageConflictError(
                "storage compare-and-swap conflict"
            )

        return deepcopy(
            validated_snapshot
        )
