from __future__ import annotations

import importlib
import inspect
import json
import unittest

from backend.storage_adapter import (
    DurableStateStore,
)

import importlib.util
from pathlib import Path


DATABASE_URL = (
    "postgresql://commit:secret"
    "@example.invalid/commit"
)

NAMESPACE = (
    "commit-backend-state"
)


def _storage_fixture():
    file_name = Path(
        "tests/test_backend_storage_adapter_contract.py"
    )

    spec = importlib.util.spec_from_file_location(
        "commit_postgres_storage_fixture",
        file_name,
    )

    if (
        spec is None
        or spec.loader is None
    ):
        raise RuntimeError(
            "unable to load storage fixture"
        )

    module = importlib.util.module_from_spec(
        spec
    )

    spec.loader.exec_module(
        module
    )

    return module


STORAGE_FIXTURE = _storage_fixture()


def _snapshot_bytes(
    *,
    finalized: bool = False,
):
    driver = (
        STORAGE_FIXTURE.FakeAtomicDriver()
    )

    store = DurableStateStore(
        driver=driver,
        namespace=NAMESPACE,
    )

    accepted = (
        STORAGE_FIXTURE._accepted_state()
    )

    store.save(
        state=accepted,
        expected_revision=0,
    )

    if finalized:
        finalized_state = (
            STORAGE_FIXTURE._finalized_state()
        )

        store.save(
            state=finalized_state,
            expected_revision=1,
        )

    return bytes(
        driver.blobs[
            NAMESPACE
        ]
    )


class FakeResult:
    def __init__(
        self,
        row,
    ):
        self._row = row

    def fetchone(
        self,
    ):
        return self._row


class FakeConnection:
    def __init__(
        self,
        *,
        rows=(),
        execute_error=None,
    ):
        self.rows = list(
            rows
        )

        self.execute_error = (
            execute_error
        )

        self.calls = []

    def __enter__(
        self,
    ):
        return self

    def __exit__(
        self,
        exc_type,
        exc,
        traceback,
    ):
        return False

    def execute(
        self,
        statement,
        parameters=(),
    ):
        self.calls.append(
            (
                str(
                    statement
                ),
                tuple(
                    parameters
                ),
            )
        )

        if (
            self.execute_error
            is not None
        ):
            raise self.execute_error

        row = (
            self.rows.pop(
                0
            )
            if self.rows
            else None
        )

        return FakeResult(
            row
        )


class FakeConnect:
    def __init__(
        self,
        connection,
        *,
        connect_error=None,
    ):
        self.connection = (
            connection
        )

        self.connect_error = (
            connect_error
        )

        self.calls = []

    def __call__(
        self,
        database_url,
        **kwargs,
    ):
        self.calls.append(
            (
                database_url,
                dict(
                    kwargs
                ),
            )
        )

        if (
            self.connect_error
            is not None
        ):
            raise self.connect_error

        return self.connection


class BackendPostgresDriverContractTests(
    unittest.TestCase
):
    @staticmethod
    def _api():
        return importlib.import_module(
            "backend.postgres_driver"
        )

    def _driver(
        self,
        *,
        rows=(),
        execute_error=None,
        connect_error=None,
    ):
        api = self._api()

        connection = FakeConnection(
            rows=rows,
            execute_error=execute_error,
        )

        connect = FakeConnect(
            connection,
            connect_error=connect_error,
        )

        driver = (
            api.PostgresAtomicDriver(
                database_url=DATABASE_URL,
                connect=connect,
            )
        )

        return (
            driver,
            connection,
            connect,
        )

    def test_public_surface_and_selected_provider_are_explicit(
        self,
    ):
        api = self._api()

        self.assertEqual(
            api.POSTGRES_DRIVER_SCHEMA,
            "commit-neon-postgres-driver-v1",
        )

        self.assertEqual(
            api.PHYSICAL_STORAGE_PROVIDER,
            "NEON_POSTGRES",
        )

        self.assertEqual(
            api.DATABASE_ENGINE,
            "POSTGRESQL",
        )

        self.assertEqual(
            api.DATABASE_DRIVER,
            "PSYCOPG_3",
        )

        self.assertEqual(
            api.POSTGRES_TABLE,
            "commit_backend_state",
        )

        self.assertTrue(
            issubclass(
                api.PostgresDriverError,
                RuntimeError,
            )
        )

        self.assertTrue(
            issubclass(
                api.PostgresDriverCorruptionError,
                api.PostgresDriverError,
            )
        )

        constructor = (
            inspect.signature(
                api.PostgresAtomicDriver
            )
        )

        self.assertEqual(
            list(
                constructor.parameters
            ),
            [
                "database_url",
                "connect",
            ],
        )

        for parameter in (
            constructor.parameters.values()
        ):
            self.assertIs(
                parameter.kind,
                inspect.Parameter.KEYWORD_ONLY,
            )

            self.assertIs(
                parameter.default,
                inspect.Parameter.empty,
            )

    def test_schema_sql_has_namespace_primary_key_revision_and_bytea(
        self,
    ):
        api = self._api()

        normalized = (
            " ".join(
                api.SCHEMA_SQL.split()
            ).upper()
        )

        self.assertIn(
            "CREATE TABLE",
            normalized,
        )

        self.assertIn(
            "COMMIT_BACKEND_STATE",
            normalized,
        )

        self.assertIn(
            "NAMESPACE TEXT PRIMARY KEY",
            normalized,
        )

        self.assertIn(
            "REVISION BIGINT NOT NULL",
            normalized,
        )

        self.assertIn(
            "PAYLOAD BYTEA NOT NULL",
            normalized,
        )

        self.assertIn(
            "CHECK (REVISION > 0)",
            normalized,
        )

    def test_missing_read_returns_none(
        self,
    ):
        driver, connection, connect = (
            self._driver(
                rows=(
                    None,
                )
            )
        )

        result = driver.read(
            namespace=NAMESPACE
        )

        self.assertIsNone(
            result
        )

        self.assertEqual(
            len(
                connection.calls
            ),
            1,
        )

        statement, parameters = (
            connection.calls[
                0
            ]
        )

        self.assertIn(
            "SELECT",
            statement.upper(),
        )

        self.assertIn(
            "REVISION",
            statement.upper(),
        )

        self.assertIn(
            "PAYLOAD",
            statement.upper(),
        )

        self.assertEqual(
            parameters,
            (
                NAMESPACE,
            ),
        )

        self.assertEqual(
            connect.calls,
            [
                (
                    DATABASE_URL,
                    {
                        "autocommit": True,
                    },
                )
            ],
        )

    def test_read_returns_exact_canonical_bytes(
        self,
    ):
        payload = (
            _snapshot_bytes()
        )

        driver, _connection, _connect = (
            self._driver(
                rows=(
                    (
                        1,
                        payload,
                    ),
                )
            )
        )

        result = driver.read(
            namespace=NAMESPACE
        )

        self.assertEqual(
            result,
            payload,
        )

        self.assertIsNot(
            result,
            payload,
        )

    def test_read_rejects_database_revision_payload_revision_mismatch(
        self,
    ):
        api = self._api()

        payload = (
            _snapshot_bytes()
        )

        driver, _connection, _connect = (
            self._driver(
                rows=(
                    (
                        2,
                        payload,
                    ),
                )
            )
        )

        with self.assertRaises(
            api.PostgresDriverCorruptionError
        ):
            driver.read(
                namespace=NAMESPACE
            )

    def test_initial_compare_and_swap_is_atomic_insert(
        self,
    ):
        payload = (
            _snapshot_bytes()
        )

        driver, connection, _connect = (
            self._driver(
                rows=(
                    (
                        1,
                    ),
                )
            )
        )

        committed = (
            driver.compare_and_swap(
                namespace=NAMESPACE,
                expected_revision=0,
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

        statement, parameters = (
            connection.calls[
                0
            ]
        )

        normalized = (
            " ".join(
                statement.split()
            ).upper()
        )

        self.assertIn(
            "INSERT INTO COMMIT_BACKEND_STATE",
            normalized,
        )

        self.assertIn(
            "ON CONFLICT",
            normalized,
        )

        self.assertIn(
            "DO NOTHING",
            normalized,
        )

        self.assertIn(
            "RETURNING REVISION",
            normalized,
        )

        self.assertEqual(
            parameters,
            (
                NAMESPACE,
                1,
                payload,
            ),
        )

    def test_update_compare_and_swap_uses_expected_revision_guard(
        self,
    ):
        payload = (
            _snapshot_bytes(
                finalized=True
            )
        )

        driver, connection, _connect = (
            self._driver(
                rows=(
                    (
                        2,
                    ),
                )
            )
        )

        committed = (
            driver.compare_and_swap(
                namespace=NAMESPACE,
                expected_revision=1,
                payload=payload,
            )
        )

        self.assertIs(
            committed,
            True,
        )

        statement, parameters = (
            connection.calls[
                0
            ]
        )

        normalized = (
            " ".join(
                statement.split()
            ).upper()
        )

        self.assertIn(
            "UPDATE COMMIT_BACKEND_STATE",
            normalized,
        )

        self.assertIn(
            "WHERE",
            normalized,
        )

        self.assertIn(
            "NAMESPACE",
            normalized,
        )

        self.assertIn(
            "REVISION",
            normalized,
        )

        self.assertIn(
            "RETURNING REVISION",
            normalized,
        )

        self.assertEqual(
            parameters,
            (
                2,
                payload,
                NAMESPACE,
                1,
            ),
        )

    def test_compare_and_swap_conflict_returns_false(
        self,
    ):
        payload = (
            _snapshot_bytes(
                finalized=True
            )
        )

        driver, _connection, _connect = (
            self._driver(
                rows=(
                    None,
                )
            )
        )

        committed = (
            driver.compare_and_swap(
                namespace=NAMESPACE,
                expected_revision=1,
                payload=payload,
            )
        )

        self.assertIs(
            committed,
            False,
        )

    def test_payload_revision_and_canonical_bytes_are_enforced_before_sql(
        self,
    ):
        api = self._api()

        canonical = (
            _snapshot_bytes()
        )

        parsed = json.loads(
            canonical.decode(
                "utf-8"
            )
        )

        mismatched = dict(
            parsed
        )

        mismatched[
            "revision"
        ] = 2

        mismatch_bytes = (
            json.dumps(
                mismatched,
                sort_keys=True,
                separators=(
                    ",",
                    ":",
                ),
            ).encode(
                "utf-8"
            )
        )

        noncanonical = (
            json.dumps(
                parsed,
                indent=2,
                sort_keys=True,
            ).encode(
                "utf-8"
            )
        )

        for payload in (
            mismatch_bytes,
            noncanonical,
        ):
            with self.subTest(
                payload=payload[:20]
            ):
                driver, connection, connect = (
                    self._driver()
                )

                with self.assertRaises(
                    api.PostgresDriverError
                ):
                    driver.compare_and_swap(
                        namespace=NAMESPACE,
                        expected_revision=0,
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

    def test_namespace_and_revision_inputs_are_strict(
        self,
    ):
        api = self._api()

        valid_payload = (
            _snapshot_bytes()
        )

        invalid_namespaces = (
            "",
            "contains\x00nul",
        )

        for namespace in invalid_namespaces:
            with self.subTest(
                namespace=repr(
                    namespace
                )
            ):
                driver, _connection, _connect = (
                    self._driver()
                )

                with self.assertRaises(
                    api.PostgresDriverError
                ):
                    driver.read(
                        namespace=namespace
                    )

        invalid_revisions = (
            True,
            -1,
            "0",
        )

        for revision in invalid_revisions:
            with self.subTest(
                revision=revision
            ):
                driver, _connection, _connect = (
                    self._driver()
                )

                with self.assertRaises(
                    api.PostgresDriverError
                ):
                    driver.compare_and_swap(
                        namespace=NAMESPACE,
                        expected_revision=revision,
                        payload=valid_payload,
                    )

    def test_database_failures_are_normalized(
        self,
    ):
        api = self._api()

        driver, _connection, _connect = (
            self._driver(
                connect_error=RuntimeError(
                    "database secret failure"
                )
            )
        )

        with self.assertRaises(
            api.PostgresDriverError
        ):
            driver.read(
                namespace=NAMESPACE
            )

        driver, _connection, _connect = (
            self._driver(
                execute_error=RuntimeError(
                    "database execute failure"
                )
            )
        )

        with self.assertRaises(
            api.PostgresDriverError
        ):
            driver.read(
                namespace=NAMESPACE
            )


if __name__ == "__main__":
    unittest.main()
