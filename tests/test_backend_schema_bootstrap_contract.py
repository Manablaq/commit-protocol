from __future__ import annotations

import importlib
import inspect
from pathlib import Path
import unittest


DATABASE_URL = (
    "postgresql://commit:"
    "secret@example.invalid/commit"
)


class FakeResult:
    pass


class FakeConnection:
    def __init__(
        self,
        *,
        execute_error=None,
    ):
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
                statement,
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

        return FakeResult()


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


class SchemaBootstrapContractTests(
    unittest.TestCase
):
    @staticmethod
    def _api():
        return importlib.import_module(
            "backend.schema_bootstrap"
        )

    def test_public_surface_and_signature_are_exact(
        self,
    ):
        api = self._api()

        self.assertEqual(
            api.SCHEMA_BOOTSTRAP_SCHEMA,
            "commit-schema-bootstrap-v1",
        )

        self.assertEqual(
            api.DATABASE_URL_ENV,
            "DATABASE_URL",
        )

        self.assertTrue(
            issubclass(
                api.SchemaBootstrapError,
                RuntimeError,
            )
        )

        signature = inspect.signature(
            api.bootstrap_schema
        )

        self.assertEqual(
            list(
                signature.parameters
            ),
            [
                "environ",
                "connect",
            ],
        )

        for parameter in (
            signature.parameters.values()
        ):
            self.assertIs(
                parameter.kind,
                inspect.Parameter.KEYWORD_ONLY,
            )

            self.assertIs(
                parameter.default,
                inspect.Parameter.empty,
            )

    def test_missing_database_configuration_fails_before_connection(
        self,
    ):
        api = self._api()

        connection = FakeConnection()

        connect = FakeConnect(
            connection
        )

        with self.assertRaises(
            api.SchemaBootstrapError
        ):
            api.bootstrap_schema(
                environ={},
                connect=connect,
            )

        self.assertEqual(
            connect.calls,
            [],
        )

        self.assertEqual(
            connection.calls,
            [],
        )

    def test_invalid_database_configuration_fails_before_connection(
        self,
    ):
        api = self._api()

        invalid = (
            "",
            "postgresql://bad\x00url",
            None,
            True,
            123,
        )

        for value in invalid:
            with self.subTest(
                value=repr(
                    value
                )
            ):
                connection = (
                    FakeConnection()
                )

                connect = FakeConnect(
                    connection
                )

                with self.assertRaises(
                    api.SchemaBootstrapError
                ):
                    api.bootstrap_schema(
                        environ={
                            api.DATABASE_URL_ENV: (
                                value
                            ),
                        },
                        connect=connect,
                    )

                self.assertEqual(
                    connect.calls,
                    [],
                )

                self.assertEqual(
                    connection.calls,
                    [],
                )

    def test_noncallable_connect_is_rejected_before_any_io(
        self,
    ):
        api = self._api()

        with self.assertRaises(
            api.SchemaBootstrapError
        ):
            api.bootstrap_schema(
                environ={
                    api.DATABASE_URL_ENV: (
                        DATABASE_URL
                    ),
                },
                connect=None,
            )

    def test_success_uses_injected_connect_and_exact_pinned_schema_once(
        self,
    ):
        api = self._api()

        from backend.postgres_driver import (
            SCHEMA_SQL,
        )

        self.assertEqual(
            api.SCHEMA_SQL,
            SCHEMA_SQL,
        )

        connection = FakeConnection()

        connect = FakeConnect(
            connection
        )

        result = api.bootstrap_schema(
            environ={
                api.DATABASE_URL_ENV: (
                    DATABASE_URL
                ),
            },
            connect=connect,
        )

        self.assertIsNone(
            result
        )

        self.assertEqual(
            connect.calls,
            [
                (
                    DATABASE_URL,
                    {
                        "autocommit": True,
                    },
                ),
            ],
        )

        self.assertEqual(
            connection.calls,
            [
                (
                    SCHEMA_SQL,
                    (),
                ),
            ],
        )

    def test_connection_failure_is_explicit_and_secret_safe(
        self,
    ):
        api = self._api()

        connection = FakeConnection()

        connect = FakeConnect(
            connection,
            connect_error=RuntimeError(
                "secret connection detail"
            ),
        )

        try:
            api.bootstrap_schema(
                environ={
                    api.DATABASE_URL_ENV: (
                        DATABASE_URL
                    ),
                },
                connect=connect,
            )
        except api.SchemaBootstrapError as exc:
            rendered = str(
                exc
            ).lower()
        else:
            self.fail(
                "connection failure was silently accepted"
            )

        self.assertNotIn(
            "secret",
            rendered,
        )

        self.assertNotIn(
            DATABASE_URL.lower(),
            rendered,
        )

        self.assertEqual(
            connection.calls,
            [],
        )

    def test_execution_failure_is_explicit_and_not_silent(
        self,
    ):
        api = self._api()

        connection = FakeConnection(
            execute_error=RuntimeError(
                "secret ddl failure detail"
            )
        )

        connect = FakeConnect(
            connection
        )

        try:
            api.bootstrap_schema(
                environ={
                    api.DATABASE_URL_ENV: (
                        DATABASE_URL
                    ),
                },
                connect=connect,
            )
        except api.SchemaBootstrapError as exc:
            rendered = str(
                exc
            ).lower()
        else:
            self.fail(
                "DDL execution failure was silently accepted"
            )

        self.assertEqual(
            len(
                connect.calls
            ),
            1,
        )

        self.assertEqual(
            len(
                connection.calls
            ),
            1,
        )

        self.assertNotIn(
            "secret",
            rendered,
        )

        self.assertNotIn(
            "ddl failure detail",
            rendered,
        )

    def test_library_has_no_global_environment_public_app_live_rpc_or_filesystem_coupling(
        self,
    ):
        self._api()

        source = Path(
            "backend/schema_bootstrap.py"
        ).read_text()

        forbidden = (
            "os.environ",
            "os.getenv",
            "psycopg.connect(",
            "FastAPI",
            "backend.service_api",
            "backend.production_app",
            "backend.network_adapter",
            "gen_call",
            "requests",
            "httpx",
            "open(",
            "Path(",
        )

        for term in forbidden:
            self.assertNotIn(
                term,
                source,
            )

    def test_public_app_and_entrypoint_do_not_import_schema_bootstrap(
        self,
    ):
        self._api()

        targets = (
            Path(
                "backend/service_api.py"
            ),
            Path(
                "backend/production_app.py"
            ),
            Path(
                "api/index.py"
            ),
        )

        for file_name in targets:
            with self.subTest(
                file_name=str(
                    file_name
                )
            ):
                source = (
                    file_name.read_text()
                )

                self.assertNotIn(
                    "schema_bootstrap",
                    source,
                )

                self.assertNotIn(
                    "SCHEMA_SQL",
                    source,
                )


if __name__ == "__main__":
    unittest.main()
