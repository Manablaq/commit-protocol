from __future__ import annotations

from contextlib import (
    redirect_stderr,
    redirect_stdout,
)
import ast
import importlib
import inspect
import io
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock, patch

from backend.ingestion_runner import (
    IngestionConflictError,
)


ENVIRON = {
    "DATABASE_URL":
        "postgresql://example.invalid/commit",

    "COMMIT_STATE_NAMESPACE":
        "commit-production",

    "GENLAYER_RPC_URL":
        "https://rpc.example.invalid",

    "COMMIT_CONTRACT_ADDRESS":
        (
            "0x"
            + "77" * 20
        ),

    "COMMIT_READER_SENDER_ADDRESS":
        (
            "0x"
            + "88" * 20
        ),
}

TX_ID = (
    "0x"
    + "ab" * 32
)


class BackendIngestionOperatorContractTests(
    unittest.TestCase
):
    @staticmethod
    def _api():
        return importlib.import_module(
            "scripts.run_backend_ingestion"
        )

    def test_public_surface_and_signature_are_exact(
        self,
    ):
        api = self._api()

        self.assertEqual(
            api.OPERATOR_SCHEMA,
            "commit-production-ingestion-operator-v1",
        )

        self.assertEqual(
            api.MODE_INDEX,
            "index",
        )

        self.assertEqual(
            api.MODE_TRANSACTION,
            "transaction",
        )

        self.assertEqual(
            api.EXIT_SUCCESS,
            0,
        )

        self.assertEqual(
            api.EXIT_FAILURE,
            1,
        )

        self.assertEqual(
            api.EXIT_USAGE,
            2,
        )

        signature = inspect.signature(
            api.main
        )

        self.assertEqual(
            list(
                signature.parameters
            ),
            [
                "argv",
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

    def test_index_mode_builds_once_and_delegates_exactly_once(
        self,
    ):
        api = self._api()

        connect = Mock(
            name="connect"
        )

        composition = Mock(
            name="composition"
        )

        composition.ingest_index.return_value = (
            {
                "fixture":
                    "saved-index",
            }
        )

        with patch.object(
            api,
            "build_production_ingestion",
            return_value=composition,
        ) as factory:
            result = api.main(
                argv=[
                    "index",
                    "--chain-id",
                    "999",
                    "--block-number",
                    "123",
                    "--state-status",
                    "finalized",
                ],
                environ=ENVIRON,
                connect=connect,
            )

        self.assertEqual(
            result,
            api.EXIT_SUCCESS,
        )

        factory.assert_called_once_with(
            environ=ENVIRON,
            connect=connect,
        )

        composition.ingest_index.assert_called_once_with(
            chain_id=999,
            block_number=123,
            state_status="finalized",
        )

        composition.ingest_transaction.assert_not_called()

    def test_transaction_mode_builds_once_and_delegates_exactly_once(
        self,
    ):
        api = self._api()

        connect = Mock(
            name="connect"
        )

        composition = Mock(
            name="composition"
        )

        composition.ingest_transaction.return_value = (
            {
                "fixture":
                    "saved-transaction",
            }
        )

        with patch.object(
            api,
            "build_production_ingestion",
            return_value=composition,
        ) as factory:
            result = api.main(
                argv=[
                    "transaction",
                    "--genlayer-tx-id",
                    TX_ID,
                ],
                environ=ENVIRON,
                connect=connect,
            )

        self.assertEqual(
            result,
            api.EXIT_SUCCESS,
        )

        factory.assert_called_once_with(
            environ=ENVIRON,
            connect=connect,
        )

        composition.ingest_transaction.assert_called_once_with(
            genlayer_tx_id=TX_ID,
        )

        composition.ingest_index.assert_not_called()

    def test_invalid_usage_returns_nonzero_before_composition(
        self,
    ):
        api = self._api()

        cases = (
            [],
            [
                "index",
            ],
            [
                "index",
                "--chain-id",
                "not-an-int",
                "--block-number",
                "123",
                "--state-status",
                "finalized",
            ],
            [
                "index",
                "--chain-id",
                "999",
                "--block-number",
                "123",
                "--state-status",
                "wrong",
            ],
            [
                "transaction",
            ],
            [
                "unknown",
            ],
        )

        for argv in cases:
            with self.subTest(
                argv=argv
            ):
                output = io.StringIO()

                with (
                    patch.object(
                        api,
                        "build_production_ingestion",
                    ) as factory,
                    redirect_stdout(
                        output
                    ),
                    redirect_stderr(
                        output
                    ),
                ):
                    result = api.main(
                        argv=argv,
                        environ=ENVIRON,
                        connect=Mock(),
                    )

                self.assertNotEqual(
                    result,
                    api.EXIT_SUCCESS,
                )

                self.assertEqual(
                    result,
                    api.EXIT_USAGE,
                )

                factory.assert_not_called()

    def test_factory_failure_is_sanitized_and_not_retried(
        self,
    ):
        api = self._api()

        output = io.StringIO()

        with (
            patch.object(
                api,
                "build_production_ingestion",
                side_effect=RuntimeError(
                    "secret database credential detail"
                ),
            ) as factory,
            redirect_stdout(
                output
            ),
            redirect_stderr(
                output
            ),
        ):
            result = api.main(
                argv=[
                    "transaction",
                    "--genlayer-tx-id",
                    TX_ID,
                ],
                environ=ENVIRON,
                connect=Mock(),
            )

        self.assertEqual(
            result,
            api.EXIT_FAILURE,
        )

        self.assertEqual(
            factory.call_count,
            1,
        )

        rendered = output.getvalue().lower()

        self.assertNotIn(
            "secret",
            rendered,
        )

        self.assertNotIn(
            "credential",
            rendered,
        )

    def test_index_failure_is_sanitized_and_not_retried(
        self,
    ):
        api = self._api()

        composition = Mock()

        composition.ingest_index.side_effect = (
            RuntimeError(
                "secret index failure detail"
            )
        )

        output = io.StringIO()

        with (
            patch.object(
                api,
                "build_production_ingestion",
                return_value=composition,
            ) as factory,
            redirect_stdout(
                output
            ),
            redirect_stderr(
                output
            ),
        ):
            result = api.main(
                argv=[
                    "index",
                    "--chain-id",
                    "999",
                    "--block-number",
                    "123",
                    "--state-status",
                    "accepted",
                ],
                environ=ENVIRON,
                connect=Mock(),
            )

        self.assertEqual(
            result,
            api.EXIT_FAILURE,
        )

        self.assertEqual(
            factory.call_count,
            1,
        )

        self.assertEqual(
            composition.ingest_index.call_count,
            1,
        )

        rendered = output.getvalue().lower()

        self.assertNotIn(
            "secret",
            rendered,
        )

        self.assertNotIn(
            "index failure detail",
            rendered,
        )

    def test_transaction_failure_is_sanitized_and_not_retried(
        self,
    ):
        api = self._api()

        composition = Mock()

        composition.ingest_transaction.side_effect = (
            RuntimeError(
                "secret receipt failure detail"
            )
        )

        output = io.StringIO()

        with (
            patch.object(
                api,
                "build_production_ingestion",
                return_value=composition,
            ) as factory,
            redirect_stdout(
                output
            ),
            redirect_stderr(
                output
            ),
        ):
            result = api.main(
                argv=[
                    "transaction",
                    "--genlayer-tx-id",
                    TX_ID,
                ],
                environ=ENVIRON,
                connect=Mock(),
            )

        self.assertEqual(
            result,
            api.EXIT_FAILURE,
        )

        self.assertEqual(
            factory.call_count,
            1,
        )

        self.assertEqual(
            composition.ingest_transaction.call_count,
            1,
        )

        rendered = output.getvalue().lower()

        self.assertNotIn(
            "secret",
            rendered,
        )

        self.assertNotIn(
            "receipt failure detail",
            rendered,
        )

    def test_conflict_failure_is_sanitized_and_not_retried(
        self,
    ):
        api = self._api()

        composition = Mock()

        composition.ingest_index.side_effect = (
            IngestionConflictError(
                "secret CAS conflict detail"
            )
        )

        output = io.StringIO()

        with (
            patch.object(
                api,
                "build_production_ingestion",
                return_value=composition,
            ),
            redirect_stdout(
                output
            ),
            redirect_stderr(
                output
            ),
        ):
            result = api.main(
                argv=[
                    "index",
                    "--chain-id",
                    "999",
                    "--block-number",
                    "123",
                    "--state-status",
                    "finalized",
                ],
                environ=ENVIRON,
                connect=Mock(),
            )

        self.assertEqual(
            result,
            api.EXIT_FAILURE,
        )

        self.assertEqual(
            composition.ingest_index.call_count,
            1,
        )

        rendered = output.getvalue().lower()

        self.assertNotIn(
            "secret",
            rendered,
        )

        self.assertNotIn(
            "cas conflict detail",
            rendered,
        )

    def test_import_has_no_database_or_network_io(
        self,
    ):
        sys.modules.pop(
            "scripts.run_backend_ingestion",
            None,
        )

        with (
            patch(
                "psycopg.connect"
            ) as connect,
            patch(
                "genlayer_py.provider.provider.requests.post"
            ) as post,
        ):
            api = importlib.import_module(
                "scripts.run_backend_ingestion"
            )

            connect.assert_not_called()
            post.assert_not_called()

        self.assertTrue(
            callable(
                api.main
            )
        )

    def test_script_guard_uses_real_environment_connector_and_process_argv(
        self,
    ):
        self._api()

        file_name = Path(
            "scripts/run_backend_ingestion.py"
        )

        source = file_name.read_text()

        tree = ast.parse(
            source
        )

        self.assertIn(
            'if __name__ == "__main__":',
            source,
        )

        self.assertIn(
            "raise SystemExit",
            source,
        )

        self.assertIn(
            "sys.argv[1:]",
            source,
        )

        self.assertIn(
            "os.environ",
            source,
        )

        self.assertIn(
            "psycopg.connect",
            source,
        )

        main_guards = [
            node
            for node in tree.body
            if isinstance(
                node,
                ast.If,
            )
        ]

        self.assertEqual(
            len(
                main_guards
            ),
            1,
        )

    def test_library_has_no_public_app_scheduler_polling_schema_or_direct_http_coupling(
        self,
    ):
        self._api()

        source = Path(
            "scripts/run_backend_ingestion.py"
        ).read_text()

        forbidden = (
            "FastAPI",
            "backend.service_api",
            "backend.production_app",
            "api/index.py",
            "SCHEMA_SQL",
            "schema_bootstrap",
            "requests.",
            "httpx.",
            "create_client",
            "while True",
            "time.sleep",
            "asyncio.sleep",
            "scheduler",
            "cron",
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
            "argparse",
            "os",
            "sys",
            "psycopg",
            "build_production_ingestion",
            "index",
            "transaction",
            "--chain-id",
            "--block-number",
            "--state-status",
            "--genlayer-tx-id",
            "accepted",
            "finalized",
        )

        for term in required:
            self.assertIn(
                term,
                source,
            )

    def test_public_application_remains_disconnected_from_operator(
        self,
    ):
        self._api()

        for file_name in (
            Path(
                "backend/service_api.py"
            ),
            Path(
                "backend/production_app.py"
            ),
            Path(
                "api/index.py"
            ),
        ):
            source = file_name.read_text()

            for forbidden in (
                "run_backend_ingestion",
                "scripts.run_backend_ingestion",
                "OPERATOR_SCHEMA",
            ):
                self.assertNotIn(
                    forbidden,
                    source,
                    msg=(
                        str(
                            file_name
                        )
                        + ":"
                        + forbidden
                    ),
                )


if __name__ == "__main__":
    unittest.main()
