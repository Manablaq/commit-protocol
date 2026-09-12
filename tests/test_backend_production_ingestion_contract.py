from __future__ import annotations

import importlib
import inspect
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock, patch

from backend.ingestion_runner import (
    IngestionConflictError,
)
from backend.postgres_driver import (
    PostgresAtomicDriver,
)
from backend.storage_adapter import (
    DurableStateStore,
)


DATABASE_URL = (
    "postgresql://example.invalid/commit"
)

STATE_NAMESPACE = (
    "commit-production"
)

RPC_URL = (
    "https://rpc.example.invalid"
)

CONTRACT_ADDRESS = (
    "0x"
    + "77" * 20
)

SENDER_ADDRESS = (
    "0x"
    + "88" * 20
)

TX_ID = (
    "0x"
    + "ab" * 32
)


def valid_environment():
    return {
        "DATABASE_URL":
            DATABASE_URL,

        "COMMIT_STATE_NAMESPACE":
            STATE_NAMESPACE,

        "GENLAYER_RPC_URL":
            RPC_URL,

        "COMMIT_CONTRACT_ADDRESS":
            CONTRACT_ADDRESS,

        "COMMIT_READER_SENDER_ADDRESS":
            SENDER_ADDRESS,
    }


class ProductionIngestionContractTests(
    unittest.TestCase
):
    @staticmethod
    def _api():
        return importlib.import_module(
            "backend.production_ingestion"
        )

    def test_public_surface_and_signatures_are_exact(
        self,
    ):
        api = self._api()

        self.assertEqual(
            api.PRODUCTION_INGESTION_SCHEMA,
            "commit-production-ingestion-v1",
        )

        self.assertEqual(
            api.DATABASE_URL_ENV,
            "DATABASE_URL",
        )

        self.assertEqual(
            api.STATE_NAMESPACE_ENV,
            "COMMIT_STATE_NAMESPACE",
        )

        self.assertEqual(
            api.RPC_URL_ENV,
            "GENLAYER_RPC_URL",
        )

        self.assertEqual(
            api.CONTRACT_ADDRESS_ENV,
            "COMMIT_CONTRACT_ADDRESS",
        )

        self.assertEqual(
            api.SENDER_ADDRESS_ENV,
            "COMMIT_READER_SENDER_ADDRESS",
        )

        self.assertTrue(
            issubclass(
                api.ProductionIngestionError,
                RuntimeError,
            )
        )

        factory_signature = (
            inspect.signature(
                api.build_production_ingestion
            )
        )

        self.assertEqual(
            list(
                factory_signature.parameters
            ),
            [
                "environ",
                "connect",
            ],
        )

        for parameter in (
            factory_signature.parameters.values()
        ):
            self.assertIs(
                parameter.kind,
                inspect.Parameter.KEYWORD_ONLY,
            )

            self.assertIs(
                parameter.default,
                inspect.Parameter.empty,
            )

        composition_signature = (
            inspect.signature(
                api.ProductionIngestion
            )
        )

        self.assertEqual(
            list(
                composition_signature.parameters
            ),
            [
                "store",
                "reader",
                "contract_address",
            ],
        )

        for parameter in (
            composition_signature.parameters.values()
        ):
            self.assertIs(
                parameter.kind,
                inspect.Parameter.KEYWORD_ONLY,
            )

            self.assertIs(
                parameter.default,
                inspect.Parameter.empty,
            )

        index_signature = (
            inspect.signature(
                api.ProductionIngestion.ingest_index
            )
        )

        self.assertEqual(
            list(
                index_signature.parameters
            ),
            [
                "self",
                "chain_id",
                "block_number",
                "state_status",
            ],
        )

        for name in (
            "chain_id",
            "block_number",
            "state_status",
        ):
            parameter = (
                index_signature.parameters[
                    name
                ]
            )

            self.assertIs(
                parameter.kind,
                inspect.Parameter.KEYWORD_ONLY,
            )

            self.assertIs(
                parameter.default,
                inspect.Parameter.empty,
            )

        transaction_signature = (
            inspect.signature(
                api.ProductionIngestion.ingest_transaction
            )
        )

        self.assertEqual(
            list(
                transaction_signature.parameters
            ),
            [
                "self",
                "genlayer_tx_id",
            ],
        )

        parameter = (
            transaction_signature.parameters[
                "genlayer_tx_id"
            ]
        )

        self.assertIs(
            parameter.kind,
            inspect.Parameter.KEYWORD_ONLY,
        )

        self.assertIs(
            parameter.default,
            inspect.Parameter.empty,
        )

    def test_factory_composes_exact_driver_store_reader_and_contract_binding(
        self,
    ):
        api = self._api()

        driver = object()
        store = object()
        reader = object()

        connect = Mock(
            name="connect"
        )

        with (
            patch.object(
                api,
                "PostgresAtomicDriver",
                return_value=driver,
            ) as driver_factory,
            patch.object(
                api,
                "DurableStateStore",
                return_value=store,
            ) as store_factory,
            patch.object(
                api,
                "build_production_live_reader",
                return_value=reader,
            ) as reader_factory,
        ):
            composition = (
                api.build_production_ingestion(
                    environ=(
                        valid_environment()
                    ),
                    connect=connect,
                )
            )

        driver_factory.assert_called_once_with(
            database_url=(
                DATABASE_URL
            ),
            connect=connect,
        )

        store_factory.assert_called_once_with(
            driver=driver,
            namespace=(
                STATE_NAMESPACE
            ),
        )

        reader_factory.assert_called_once_with(
            environ=(
                valid_environment()
            )
        )

        self.assertIsInstance(
            composition,
            api.ProductionIngestion,
        )

        self.assertIs(
            composition._store,
            store,
        )

        self.assertIs(
            composition._reader,
            reader,
        )

        self.assertEqual(
            composition._contract_address,
            CONTRACT_ADDRESS,
        )

        connect.assert_not_called()

    def test_factory_with_real_components_performs_zero_database_and_rpc_io(
        self,
    ):
        api = self._api()

        connect_calls = []

        def connect(
            *args,
            **kwargs,
        ):
            connect_calls.append(
                {
                    "args":
                        args,

                    "kwargs":
                        kwargs,
                }
            )

            raise AssertionError(
                "database connection occurred during composition"
            )

        with patch(
            "genlayer_py.provider.provider.requests.post"
        ) as post:
            composition = (
                api.build_production_ingestion(
                    environ=(
                        valid_environment()
                    ),
                    connect=connect,
                )
            )

            post.assert_not_called()

        self.assertEqual(
            connect_calls,
            [],
        )

        self.assertIsInstance(
            composition._store,
            DurableStateStore,
        )

        self.assertIsInstance(
            composition._store._driver,
            PostgresAtomicDriver,
        )

        self.assertEqual(
            composition._store._namespace,
            STATE_NAMESPACE,
        )

        provider = (
            composition._reader._make_request.__self__
        )

        self.assertEqual(
            provider.url,
            RPC_URL,
        )

    def test_all_invalid_configuration_fails_before_composition_dependencies(
        self,
    ):
        api = self._api()

        valid = (
            valid_environment()
        )

        cases = [
            (
                "none-environ",
                None,
                Mock(),
            ),
            (
                "non-mapping-environ",
                [],
                Mock(),
            ),
            (
                "noncallable-connect",
                valid,
                None,
            ),
        ]

        for key in (
            "DATABASE_URL",
            "COMMIT_STATE_NAMESPACE",
            "GENLAYER_RPC_URL",
            "COMMIT_CONTRACT_ADDRESS",
            "COMMIT_READER_SENDER_ADDRESS",
        ):
            missing = dict(
                valid
            )

            missing.pop(
                key
            )

            cases.append(
                (
                    "missing-"
                    + key,
                    missing,
                    Mock(),
                )
            )

            blank = dict(
                valid
            )

            blank[
                key
            ] = "   "

            cases.append(
                (
                    "blank-"
                    + key,
                    blank,
                    Mock(),
                )
            )

            nonstring = dict(
                valid
            )

            nonstring[
                key
            ] = 123

            cases.append(
                (
                    "nonstring-"
                    + key,
                    nonstring,
                    Mock(),
                )
            )

        for label, environ, connect in cases:
            with self.subTest(
                label=label
            ):
                with (
                    patch.object(
                        api,
                        "PostgresAtomicDriver",
                    ) as driver_factory,
                    patch.object(
                        api,
                        "DurableStateStore",
                    ) as store_factory,
                    patch.object(
                        api,
                        "build_production_live_reader",
                    ) as reader_factory,
                ):
                    with self.assertRaises(
                        api.ProductionIngestionError
                    ):
                        api.build_production_ingestion(
                            environ=environ,
                            connect=connect,
                        )

                    driver_factory.assert_not_called()
                    store_factory.assert_not_called()
                    reader_factory.assert_not_called()

    def test_composition_dependency_failure_is_sanitized(
        self,
    ):
        api = self._api()

        with patch.object(
            api,
            "PostgresAtomicDriver",
            side_effect=RuntimeError(
                "secret database composition detail"
            ),
        ):
            try:
                api.build_production_ingestion(
                    environ=(
                        valid_environment()
                    ),
                    connect=Mock(),
                )
            except api.ProductionIngestionError as exc:
                rendered = str(
                    exc
                ).lower()
            else:
                self.fail(
                    "composition dependency failure was accepted"
                )

        self.assertNotIn(
            "secret",
            rendered,
        )

        self.assertNotIn(
            "database composition detail",
            rendered,
        )

    def test_index_ingestion_delegates_exactly_once_without_retry(
        self,
    ):
        api = self._api()

        store = object()
        reader = object()

        composition = api.ProductionIngestion(
            store=store,
            reader=reader,
            contract_address=(
                CONTRACT_ADDRESS
            ),
        )

        expected = object()

        with patch.object(
            api,
            "ingest_index_observation",
            return_value=expected,
        ) as ingest:
            result = (
                composition.ingest_index(
                    chain_id=999,
                    block_number=123,
                    state_status=(
                        "finalized"
                    ),
                )
            )

        self.assertIs(
            result,
            expected,
        )

        ingest.assert_called_once_with(
            store=store,
            reader=reader,
            chain_id=999,
            contract_address=(
                CONTRACT_ADDRESS
            ),
            block_number=123,
            state_status=(
                "finalized"
            ),
        )

    def test_transaction_ingestion_fetches_receipt_then_delegates_exactly_once(
        self,
    ):
        api = self._api()

        events = []

        store = object()

        class Reader:
            def get_transaction_receipt(
                self,
                *,
                genlayer_tx_id,
            ):
                events.append(
                    (
                        "receipt",
                        {
                            "genlayer_tx_id":
                                genlayer_tx_id,
                        },
                    )
                )

                return {
                    "genlayer_tx_id":
                        genlayer_tx_id,

                    "status_code":
                        7,

                    "status_name":
                        "Finalized",

                    "execution_result":
                        "FINISHED_WITH_RETURN",
                }

        reader = Reader()

        composition = api.ProductionIngestion(
            store=store,
            reader=reader,
            contract_address=(
                CONTRACT_ADDRESS
            ),
        )

        expected = object()

        def ingest(
            **kwargs,
        ):
            events.append(
                (
                    "ingest",
                    kwargs,
                )
            )

            return expected

        with patch.object(
            api,
            "ingest_transaction_observation",
            side_effect=ingest,
        ) as ingest_mock:
            result = (
                composition.ingest_transaction(
                    genlayer_tx_id=(
                        TX_ID
                    )
                )
            )

        self.assertIs(
            result,
            expected,
        )

        ingest_mock.assert_called_once_with(
            store=store,
            genlayer_tx_id=(
                TX_ID
            ),
            status_code=7,
            status_name=(
                "Finalized"
            ),
            execution_result=(
                "FINISHED_WITH_RETURN"
            ),
        )

        self.assertEqual(
            events,
            [
                (
                    "receipt",
                    {
                        "genlayer_tx_id":
                            TX_ID,
                    },
                ),
                (
                    "ingest",
                    {
                        "store":
                            store,

                        "genlayer_tx_id":
                            TX_ID,

                        "status_code":
                            7,

                        "status_name":
                            "Finalized",

                        "execution_result":
                            "FINISHED_WITH_RETURN",
                    },
                ),
            ],
        )

    def test_transaction_receipt_failure_never_calls_ingestion_and_has_no_retry(
        self,
    ):
        api = self._api()

        calls = []

        class Reader:
            def get_transaction_receipt(
                self,
                *,
                genlayer_tx_id,
            ):
                calls.append(
                    genlayer_tx_id
                )

                raise RuntimeError(
                    "receipt unavailable"
                )

        composition = api.ProductionIngestion(
            store=object(),
            reader=Reader(),
            contract_address=(
                CONTRACT_ADDRESS
            ),
        )

        with patch.object(
            api,
            "ingest_transaction_observation",
        ) as ingest:
            with self.assertRaises(
                RuntimeError
            ):
                composition.ingest_transaction(
                    genlayer_tx_id=(
                        TX_ID
                    )
                )

            ingest.assert_not_called()

        self.assertEqual(
            calls,
            [
                TX_ID,
            ],
        )

    def test_ingestion_conflicts_propagate_exactly_and_are_never_retried(
        self,
    ):
        api = self._api()

        composition = api.ProductionIngestion(
            store=object(),
            reader=object(),
            contract_address=(
                CONTRACT_ADDRESS
            ),
        )

        with patch.object(
            api,
            "ingest_index_observation",
            side_effect=(
                IngestionConflictError(
                    "durable state conflict"
                )
            ),
        ) as index_ingest:
            with self.assertRaises(
                IngestionConflictError
            ):
                composition.ingest_index(
                    chain_id=999,
                    block_number=123,
                    state_status=(
                        "finalized"
                    ),
                )

            self.assertEqual(
                index_ingest.call_count,
                1,
            )

        class ReceiptReader:
            def get_transaction_receipt(
                self,
                *,
                genlayer_tx_id,
            ):
                return {
                    "genlayer_tx_id":
                        genlayer_tx_id,

                    "status_code":
                        7,

                    "status_name":
                        "Finalized",

                    "execution_result":
                        "FINISHED_WITH_RETURN",
                }

        composition = api.ProductionIngestion(
            store=object(),
            reader=ReceiptReader(),
            contract_address=(
                CONTRACT_ADDRESS
            ),
        )

        with patch.object(
            api,
            "ingest_transaction_observation",
            side_effect=(
                IngestionConflictError(
                    "durable state conflict"
                )
            ),
        ) as transaction_ingest:
            with self.assertRaises(
                IngestionConflictError
            ):
                composition.ingest_transaction(
                    genlayer_tx_id=(
                        TX_ID
                    )
                )

            self.assertEqual(
                transaction_ingest.call_count,
                1,
            )

    def test_library_has_no_global_environment_schema_public_app_polling_scheduler_or_direct_io_coupling(
        self,
    ):
        self._api()

        source = Path(
            "backend/production_ingestion.py"
        ).read_text()

        forbidden = (
            "os.environ",
            "os.getenv",
            "psycopg.connect(",
            "SCHEMA_SQL",
            "schema_bootstrap",
            "FastAPI",
            "backend.service_api",
            "api/index.py",
            "requests.",
            "httpx.",
            "create_client",
            "time.sleep",
            "asyncio.sleep",
            "while True",
            "schedule",
            "scheduler",
            "poll(",
            "retry(",
            "gen_getTransactionStatus",
            "transaction_hash_variant",
            "application_decision",
        )

        for term in forbidden:
            self.assertNotIn(
                term,
                source,
            )

        required = (
            "PostgresAtomicDriver",
            "DurableStateStore",
            "build_production_live_reader",
            "ingest_index_observation",
            "ingest_transaction_observation",
            "DATABASE_URL",
            "COMMIT_STATE_NAMESPACE",
            "GENLAYER_RPC_URL",
            "COMMIT_CONTRACT_ADDRESS",
            "COMMIT_READER_SENDER_ADDRESS",
        )

        for term in required:
            self.assertIn(
                term,
                source,
            )

    def test_public_application_remains_disconnected_from_production_ingestion(
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

        forbidden = (
            "production_ingestion",
            "ProductionIngestion",
            "build_production_ingestion",
            "ingest_index_observation",
            "ingest_transaction_observation",
        )

        for file_name in targets:
            source = file_name.read_text()

            for term in forbidden:
                self.assertNotIn(
                    term,
                    source,
                    msg=(
                        str(
                            file_name
                        )
                        + ":"
                        + term
                    ),
                )


if __name__ == "__main__":
    unittest.main()
