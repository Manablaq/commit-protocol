from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import unittest

import backend.postgres_driver as api


POSTGRES_BIGINT_MAX = (
    2**63
    - 1
)


def _fixture():
    file_name = Path(
        "tests/test_backend_postgres_driver_contract.py"
    )

    spec = importlib.util.spec_from_file_location(
        "commit_postgres_integrity_fixture",
        file_name,
    )

    if (
        spec is None
        or spec.loader is None
    ):
        raise RuntimeError(
            "unable to load postgres driver fixture"
        )

    module = importlib.util.module_from_spec(
        spec
    )

    spec.loader.exec_module(
        module
    )

    return module


FIXTURE = _fixture()


def _payload_with_revision(
    revision: int,
) -> bytes:
    value = json.loads(
        FIXTURE._snapshot_bytes().decode(
            "utf-8"
        )
    )

    value[
        "revision"
    ] = revision

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


def _driver(
    *,
    rows=(),
):
    connection = (
        FIXTURE.FakeConnection(
            rows=rows
        )
    )

    connect = (
        FIXTURE.FakeConnect(
            connection
        )
    )

    driver = (
        api.PostgresAtomicDriver(
            database_url=(
                FIXTURE.DATABASE_URL
            ),
            connect=connect,
        )
    )

    return (
        driver,
        connection,
        connect,
    )


class BackendPostgresDriverIntegrityTests(
    unittest.TestCase
):
    def test_postgres_bigint_bound_is_explicit(
        self,
    ):
        self.assertEqual(
            api.POSTGRES_BIGINT_MAX,
            POSTGRES_BIGINT_MAX,
        )

    def test_expected_revision_at_bigint_max_is_rejected_before_connection(
        self,
    ):
        driver, connection, connect = (
            _driver(
                rows=(
                    (
                        POSTGRES_BIGINT_MAX
                        + 1,
                    ),
                )
            )
        )

        payload = (
            _payload_with_revision(
                POSTGRES_BIGINT_MAX
                + 1
            )
        )

        with self.assertRaises(
            api.PostgresDriverError
        ):
            driver.compare_and_swap(
                namespace=(
                    FIXTURE.NAMESPACE
                ),
                expected_revision=(
                    POSTGRES_BIGINT_MAX
                ),
                payload=payload,
            )

        self.assertEqual(
            connection.calls,
            [],
        )

        self.assertEqual(
            connect.calls,
            [],
        )

    def test_read_rejects_revision_above_postgres_bigint_max(
        self,
    ):
        payload = (
            _payload_with_revision(
                POSTGRES_BIGINT_MAX
                + 1
            )
        )

        driver, _connection, _connect = (
            _driver(
                rows=(
                    (
                        POSTGRES_BIGINT_MAX
                        + 1,
                        payload,
                    ),
                )
            )
        )

        with self.assertRaises(
            api.PostgresDriverCorruptionError
        ):
            driver.read(
                namespace=(
                    FIXTURE.NAMESPACE
                )
            )

    def test_maximum_postgres_bigint_revision_is_valid_on_read(
        self,
    ):
        payload = (
            _payload_with_revision(
                POSTGRES_BIGINT_MAX
            )
        )

        driver, _connection, _connect = (
            _driver(
                rows=(
                    (
                        POSTGRES_BIGINT_MAX,
                        payload,
                    ),
                )
            )
        )

        self.assertEqual(
            driver.read(
                namespace=(
                    FIXTURE.NAMESPACE
                )
            ),
            payload,
        )

    def test_max_minus_one_can_atomically_promote_to_bigint_max(
        self,
    ):
        payload = (
            _payload_with_revision(
                POSTGRES_BIGINT_MAX
            )
        )

        driver, connection, _connect = (
            _driver(
                rows=(
                    (
                        POSTGRES_BIGINT_MAX,
                    ),
                )
            )
        )

        committed = (
            driver.compare_and_swap(
                namespace=(
                    FIXTURE.NAMESPACE
                ),
                expected_revision=(
                    POSTGRES_BIGINT_MAX
                    - 1
                ),
                payload=payload,
            )
        )

        self.assertIs(
            committed,
            True,
        )

        self.assertEqual(
            len(
                connection.calls
            ),
            1,
        )

    def test_namespace_content_remains_parameterized(
        self,
    ):
        malicious_namespace = (
            "x'; DROP TABLE "
            "commit_backend_state; --"
        )

        driver, connection, _connect = (
            _driver(
                rows=(
                    None,
                )
            )
        )

        self.assertIsNone(
            driver.read(
                namespace=(
                    malicious_namespace
                )
            )
        )

        statement, parameters = (
            connection.calls[
                0
            ]
        )

        self.assertNotIn(
            malicious_namespace,
            statement,
        )

        self.assertEqual(
            parameters,
            (
                malicious_namespace,
            ),
        )

    def test_malformed_cas_return_revision_is_rejected(
        self,
    ):
        payload = (
            FIXTURE._snapshot_bytes()
        )

        driver, _connection, _connect = (
            _driver(
                rows=(
                    (
                        999,
                    ),
                )
            )
        )

        with self.assertRaises(
            api.PostgresDriverCorruptionError
        ):
            driver.compare_and_swap(
                namespace=(
                    FIXTURE.NAMESPACE
                ),
                expected_revision=0,
                payload=payload,
            )

    def test_malformed_read_row_is_rejected(
        self,
    ):
        payload = (
            FIXTURE._snapshot_bytes()
        )

        driver, _connection, _connect = (
            _driver(
                rows=(
                    (
                        1,
                        payload,
                        "unexpected",
                    ),
                )
            )
        )

        with self.assertRaises(
            api.PostgresDriverCorruptionError
        ):
            driver.read(
                namespace=(
                    FIXTURE.NAMESPACE
                )
            )


if __name__ == "__main__":
    unittest.main()
