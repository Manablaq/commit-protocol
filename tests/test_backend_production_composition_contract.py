from __future__ import annotations

import importlib
import importlib.util
import inspect
from pathlib import Path
from unittest.mock import patch
from urllib.parse import urlencode
import unittest


DATABASE_URL = (
    "postgresql://commit:"
    "secret@example.invalid/commit"
)

STATE_NAMESPACE = (
    "commit-production-state"
)


def _service_fixture():
    file_name = Path(
        "tests/test_backend_service_api_contract.py"
    )

    spec = importlib.util.spec_from_file_location(
        "commit_production_service_fixture",
        file_name,
    )

    if (
        spec is None
        or spec.loader is None
    ):
        raise RuntimeError(
            "unable to load service fixture"
        )

    module = importlib.util.module_from_spec(
        spec
    )

    spec.loader.exec_module(
        module
    )

    return module


SERVICE_FIXTURE = _service_fixture()


class ProductionCompositionContractTests(
    unittest.TestCase
):
    @staticmethod
    def _api():
        return importlib.import_module(
            "backend.production_app"
        )

    def test_public_surface_and_signature_are_exact(
        self,
    ):
        api = self._api()

        self.assertEqual(
            api.PRODUCTION_COMPOSITION_SCHEMA,
            "commit-production-composition-v1",
        )

        self.assertEqual(
            api.DATABASE_URL_ENV,
            "DATABASE_URL",
        )

        self.assertEqual(
            api.STATE_NAMESPACE_ENV,
            "COMMIT_STATE_NAMESPACE",
        )

        self.assertTrue(
            issubclass(
                api.ProductionCompositionError,
                RuntimeError,
            )
        )

        signature = inspect.signature(
            api.build_production_app
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

    def test_missing_database_url_fails_before_connection(
        self,
    ):
        api = self._api()

        calls = []

        def connect(
            *args,
            **kwargs,
        ):
            calls.append(
                (
                    args,
                    kwargs,
                )
            )

            raise AssertionError(
                "connect must not run"
            )

        with self.assertRaises(
            api.ProductionCompositionError
        ):
            api.build_production_app(
                environ={
                    api.STATE_NAMESPACE_ENV: (
                        STATE_NAMESPACE
                    ),
                },
                connect=connect,
            )

        self.assertEqual(
            calls,
            [],
        )

    def test_missing_state_namespace_fails_before_connection(
        self,
    ):
        api = self._api()

        calls = []

        def connect(
            *args,
            **kwargs,
        ):
            calls.append(
                (
                    args,
                    kwargs,
                )
            )

            raise AssertionError(
                "connect must not run"
            )

        with self.assertRaises(
            api.ProductionCompositionError
        ):
            api.build_production_app(
                environ={
                    api.DATABASE_URL_ENV: (
                        DATABASE_URL
                    ),
                },
                connect=connect,
            )

        self.assertEqual(
            calls,
            [],
        )

    def test_empty_or_nul_configuration_is_rejected_before_connection(
        self,
    ):
        api = self._api()

        invalid_cases = (
            (
                "",
                STATE_NAMESPACE,
            ),
            (
                "postgresql://bad\x00url",
                STATE_NAMESPACE,
            ),
            (
                DATABASE_URL,
                "",
            ),
            (
                DATABASE_URL,
                "bad\x00namespace",
            ),
        )

        for (
            database_url,
            namespace,
        ) in invalid_cases:
            with self.subTest(
                database_url=repr(
                    database_url
                ),
                namespace=repr(
                    namespace
                ),
            ):
                calls = []

                def connect(
                    *args,
                    **kwargs,
                ):
                    calls.append(
                        (
                            args,
                            kwargs,
                        )
                    )

                    raise AssertionError(
                        "connect must not run"
                    )

                with self.assertRaises(
                    api.ProductionCompositionError
                ):
                    api.build_production_app(
                        environ={
                            api.DATABASE_URL_ENV: (
                                database_url
                            ),
                            api.STATE_NAMESPACE_ENV: (
                                namespace
                            ),
                        },
                        connect=connect,
                    )

                self.assertEqual(
                    calls,
                    [],
                )

    def test_composition_order_and_dependency_injection_are_exact(
        self,
    ):
        api = self._api()

        events = []

        connect = object()
        driver = object()
        store = object()
        application = object()

        def driver_factory(
            *,
            database_url,
            connect,
        ):
            events.append(
                (
                    "driver",
                    database_url,
                    connect,
                )
            )

            return driver

        def store_factory(
            *,
            driver,
            namespace,
        ):
            events.append(
                (
                    "store",
                    driver,
                    namespace,
                )
            )

            return store

        def app_factory(
            *,
            store,
        ):
            events.append(
                (
                    "app",
                    store,
                )
            )

            return application

        with (
            patch.object(
                api,
                "PostgresAtomicDriver",
                side_effect=driver_factory,
            ),
            patch.object(
                api,
                "DurableStateStore",
                side_effect=store_factory,
            ),
            patch.object(
                api,
                "create_app",
                side_effect=app_factory,
            ),
        ):
            result = (
                api.build_production_app(
                    environ={
                        api.DATABASE_URL_ENV: (
                            DATABASE_URL
                        ),
                        api.STATE_NAMESPACE_ENV: (
                            STATE_NAMESPACE
                        ),
                    },
                    connect=connect,
                )
            )

        self.assertIs(
            result,
            application,
        )

        self.assertEqual(
            events,
            [
                (
                    "driver",
                    DATABASE_URL,
                    connect,
                ),
                (
                    "store",
                    driver,
                    STATE_NAMESPACE,
                ),
                (
                    "app",
                    store,
                ),
            ],
        )

    def test_composition_creates_app_without_opening_database_connection(
        self,
    ):
        api = self._api()

        calls = []

        def forbidden_connect(
            *args,
            **kwargs,
        ):
            calls.append(
                (
                    args,
                    kwargs,
                )
            )

            raise AssertionError(
                "composition opened database connection"
            )

        app = api.build_production_app(
            environ={
                api.DATABASE_URL_ENV: (
                    DATABASE_URL
                ),
                api.STATE_NAMESPACE_ENV: (
                    STATE_NAMESPACE
                ),
            },
            connect=forbidden_connect,
        )

        public = {}

        for route in app.routes:
            path = getattr(
                route,
                "path",
                "",
            )

            if not path.startswith(
                "/api/v1"
            ):
                continue

            public[
                path
            ] = set(
                getattr(
                    route,
                    "methods",
                    set(),
                )
            )

        self.assertEqual(
            public,
            {
                "/api/v1/health": {
                    "GET",
                },
                "/api/v1/index": {
                    "GET",
                },
                (
                    "/api/v1/transactions/"
                    "{"
                    "gen"
                    "layer_tx_id"
                    "}"
                ): {
                    "GET",
                },
            },
        )

        self.assertEqual(
            calls,
            [],
        )

    def test_configuration_errors_do_not_leak_secret_values(
        self,
    ):
        api = self._api()

        secret_url = (
            "postgresql://"
            "highly-sensitive-password"
            "\x00@example.invalid/db"
        )

        try:
            api.build_production_app(
                environ={
                    api.DATABASE_URL_ENV: (
                        secret_url
                    ),
                    api.STATE_NAMESPACE_ENV: (
                        STATE_NAMESPACE
                    ),
                },
                connect=lambda *args, **kwargs: None,
            )
        except api.ProductionCompositionError as exc:
            rendered = str(
                exc
            ).lower()
        else:
            self.fail(
                "invalid secret-bearing configuration was accepted"
            )

        self.assertNotIn(
            "highly-sensitive-password",
            rendered,
        )

        self.assertNotIn(
            secret_url.lower(),
            rendered,
        )

    def test_library_composition_has_no_global_environment_or_io_coupling(
        self,
    ):
        self._api()

        source = Path(
            "backend/production_app.py"
        ).read_text()

        forbidden = (
            "os.environ",
            "os.getenv",
            "environ.get(",
            "psycopg.connect(",
            "SCHEMA_SQL",
            "CREATE TABLE",
            "sqlite",
            "requests",
            "httpx",
            "gen_call",
            "backend.network_adapter",
            "open(",
            "Path(",
        )

        for term in forbidden:
            self.assertNotIn(
                term,
                source,
            )

    def test_client_cannot_select_storage_namespace_through_public_routes(
        self,
    ):
        api = self._api()

        app = api.build_production_app(
            environ={
                api.DATABASE_URL_ENV: (
                    DATABASE_URL
                ),
                api.STATE_NAMESPACE_ENV: (
                    STATE_NAMESPACE
                ),
            },
            connect=lambda *args, **kwargs: (
                None
            ),
        )

        route_parameters = set()

        for route in app.routes:
            path = getattr(
                route,
                "path",
                "",
            )

            if not path.startswith(
                "/api/v1"
            ):
                continue

            dependant = getattr(
                route,
                "dependant",
                None,
            )

            if dependant is None:
                continue

            for collection_name in (
                "path_params",
                "query_params",
                "header_params",
                "cookie_params",
            ):
                for field in getattr(
                    dependant,
                    collection_name,
                    (),
                ):
                    route_parameters.add(
                        field.name
                    )

        self.assertNotIn(
            api.STATE_NAMESPACE_ENV,
            route_parameters,
        )

        self.assertNotIn(
            "namespace",
            route_parameters,
        )

    def test_database_connection_failure_is_deferred_and_fails_closed(
        self,
    ):
        api = self._api()

        calls = []

        def broken_connect(
            *args,
            **kwargs,
        ):
            calls.append(
                (
                    args,
                    kwargs,
                )
            )

            raise RuntimeError(
                "secret database failure detail"
            )

        app = api.build_production_app(
            environ={
                api.DATABASE_URL_ENV: (
                    DATABASE_URL
                ),
                api.STATE_NAMESPACE_ENV: (
                    STATE_NAMESPACE
                ),
            },
            connect=broken_connect,
        )

        self.assertEqual(
            calls,
            [],
            "database connection occurred during composition",
        )

        query = urlencode(
            {
                "chain_id": (
                    SERVICE_FIXTURE.CHAIN_ID
                ),
                "contract_address": (
                    SERVICE_FIXTURE.CONTRACT_ADDRESS
                ),
                "state_basis": (
                    "FINALIZED"
                ),
            }
        )

        status, body = (
            SERVICE_FIXTURE._request(
                app,
                path="/api/v1/index",
                query=query,
            )
        )

        self.assertEqual(
            status,
            503,
        )

        self.assertEqual(
            body,
            {
                "schema": (
                    "commit-backend-service-error-v1"
                ),
                "error": (
                    "BACKEND_STATE_UNAVAILABLE"
                ),
            },
        )

        self.assertEqual(
            len(
                calls
            ),
            1,
        )

        rendered = repr(
            body
        ).lower()

        self.assertNotIn(
            "secret",
            rendered,
        )

        self.assertNotIn(
            "database failure detail",
            rendered,
        )


if __name__ == "__main__":
    unittest.main()
