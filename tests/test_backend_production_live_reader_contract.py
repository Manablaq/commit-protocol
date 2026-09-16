from __future__ import annotations

import importlib
import inspect
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

import eth_utils

from genlayer_py.abi import calldata
from genlayer_py.abi.transactions import (
    serialize,
)
from genlayer_py.contracts.utils import (
    make_calldata_object,
)
from genlayer_py.provider.provider import (
    GenLayerProvider,
)

from backend.live_reader import (
    GenLayerPinnedReader,
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
        "GENLAYER_RPC_URL": (
            RPC_URL
        ),
        "COMMIT_CONTRACT_ADDRESS": (
            CONTRACT_ADDRESS
        ),
        "COMMIT_READER_SENDER_ADDRESS": (
            SENDER_ADDRESS
        ),
    }


class FakeProvider:
    def __init__(
        self,
        url,
    ):
        self.url = url
        self.calls = []
        self.handler = None

    def make_request(
        self,
        *,
        method,
        params,
    ):
        self.calls.append(
            {
                "method": method,
                "params": params,
            }
        )

        if self.handler is None:
            raise AssertionError(
                "fake provider handler not configured"
            )

        return self.handler(
            method=method,
            params=params,
        )


class ProductionLiveReaderContractTests(
    unittest.TestCase
):
    @staticmethod
    def _api():
        return importlib.import_module(
            "backend.production_live_reader"
        )

    def test_public_surface_and_signature_are_exact(
        self,
    ):
        api = self._api()

        self.assertEqual(
            api.PRODUCTION_LIVE_READER_SCHEMA,
            "commit-production-live-reader-v1",
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
                api.ProductionLiveReaderError,
                RuntimeError,
            )
        )

        self.assertIs(
            api.GenLayerProvider,
            GenLayerProvider,
        )

        signature = inspect.signature(
            api.build_production_live_reader
        )

        self.assertEqual(
            list(
                signature.parameters
            ),
            [
                "environ",
            ],
        )

        parameter = signature.parameters[
            "environ"
        ]

        self.assertIs(
            parameter.kind,
            inspect.Parameter.KEYWORD_ONLY,
        )

        self.assertIs(
            parameter.default,
            inspect.Parameter.empty,
        )

    def test_valid_config_constructs_exactly_one_provider_and_reader(
        self,
    ):
        api = self._api()

        provider = FakeProvider(
            RPC_URL
        )

        with patch.object(
            api,
            "GenLayerProvider",
            return_value=provider,
        ) as provider_factory:
            reader = (
                api.build_production_live_reader(
                    environ=(
                        valid_environment()
                    )
                )
            )

        provider_factory.assert_called_once_with(
            RPC_URL
        )

        self.assertIsInstance(
            reader,
            GenLayerPinnedReader,
        )

        self.assertIs(
            reader._make_request.__self__,
            provider,
        )

        self.assertEqual(
            reader._contract_address,
            CONTRACT_ADDRESS,
        )

        self.assertEqual(
            reader._sender_address,
            SENDER_ADDRESS,
        )

    def test_module_import_and_actual_provider_construction_have_zero_network_io(
        self,
    ):
        sys.modules.pop(
            "backend.production_live_reader",
            None,
        )

        with patch(
            "genlayer_py.provider.provider.requests.post"
        ) as post:
            api = (
                importlib.import_module(
                    "backend.production_live_reader"
                )
            )

            reader = (
                api.build_production_live_reader(
                    environ=(
                        valid_environment()
                    )
                )
            )

            post.assert_not_called()

        self.assertIsInstance(
            reader,
            GenLayerPinnedReader,
        )

        provider = (
            reader._make_request.__self__
        )

        self.assertIsInstance(
            provider,
            GenLayerProvider,
        )

        self.assertEqual(
            provider.url,
            RPC_URL,
        )

    def test_all_invalid_config_fails_before_provider_construction(
        self,
    ):
        api = self._api()

        cases = (
            (
                "none-environ",
                None,
            ),
            (
                "empty-environ",
                {},
            ),
            (
                "missing-rpc",
                {
                    "COMMIT_CONTRACT_ADDRESS":
                        CONTRACT_ADDRESS,
                    "COMMIT_READER_SENDER_ADDRESS":
                        SENDER_ADDRESS,
                },
            ),
            (
                "missing-contract",
                {
                    "GENLAYER_RPC_URL":
                        RPC_URL,
                    "COMMIT_READER_SENDER_ADDRESS":
                        SENDER_ADDRESS,
                },
            ),
            (
                "missing-sender",
                {
                    "GENLAYER_RPC_URL":
                        RPC_URL,
                    "COMMIT_CONTRACT_ADDRESS":
                        CONTRACT_ADDRESS,
                },
            ),
            (
                "blank-rpc",
                {
                    **valid_environment(),
                    "GENLAYER_RPC_URL":
                        "",
                },
            ),
            (
                "whitespace-rpc",
                {
                    **valid_environment(),
                    "GENLAYER_RPC_URL":
                        "   ",
                },
            ),
            (
                "non-string-rpc",
                {
                    **valid_environment(),
                    "GENLAYER_RPC_URL":
                        123,
                },
            ),
            (
                "unsupported-rpc-scheme",
                {
                    **valid_environment(),
                    "GENLAYER_RPC_URL":
                        "ftp://rpc.example.invalid",
                },
            ),
            (
                "rpc-without-host",
                {
                    **valid_environment(),
                    "GENLAYER_RPC_URL":
                        "https://",
                },
            ),
            (
                "blank-contract",
                {
                    **valid_environment(),
                    "COMMIT_CONTRACT_ADDRESS":
                        "",
                },
            ),
            (
                "invalid-contract",
                {
                    **valid_environment(),
                    "COMMIT_CONTRACT_ADDRESS":
                        "0x1234",
                },
            ),
            (
                "blank-sender",
                {
                    **valid_environment(),
                    "COMMIT_READER_SENDER_ADDRESS":
                        "",
                },
            ),
            (
                "invalid-sender",
                {
                    **valid_environment(),
                    "COMMIT_READER_SENDER_ADDRESS":
                        "not-an-address",
                },
            ),
        )

        for label, environ in cases:
            with self.subTest(
                label=label
            ):
                with patch.object(
                    api,
                    "GenLayerProvider",
                ) as provider_factory:
                    with self.assertRaises(
                        api.ProductionLiveReaderError
                    ):
                        api.build_production_live_reader(
                            environ=environ
                        )

                    provider_factory.assert_not_called()

    def test_provider_construction_failure_is_sanitized(
        self,
    ):
        api = self._api()

        with patch.object(
            api,
            "GenLayerProvider",
            side_effect=RuntimeError(
                "secret provider endpoint token"
            ),
        ) as provider_factory:
            try:
                api.build_production_live_reader(
                    environ=(
                        valid_environment()
                    )
                )
            except api.ProductionLiveReaderError as exc:
                rendered = str(
                    exc
                ).lower()
            else:
                self.fail(
                    "provider construction failure was accepted"
                )

        provider_factory.assert_called_once_with(
            RPC_URL
        )

        self.assertNotIn(
            "secret",
            rendered,
        )

        self.assertNotIn(
            "endpoint token",
            rendered,
        )

    def test_composed_encoder_matches_pinned_sdk_envelope_exactly(
        self,
    ):
        api = self._api()

        reader = (
            api.build_production_live_reader(
                environ=(
                    valid_environment()
                )
            )
        )

        actual = reader._encode_call(
            function_name=(
                "protocol_info"
            ),
            args=(),
        )

        expected = serialize(
            [
                calldata.encode(
                    make_calldata_object(
                        method=(
                            "protocol_info"
                        ),
                        args=(),
                        kwargs=None,
                    )
                ),
                b"\x00",
            ]
        )

        self.assertEqual(
            actual,
            expected,
        )

        self.assertIsInstance(
            actual,
            str,
        )

        self.assertTrue(
            actual.startswith(
                "0x"
            )
        )

    def test_composed_decoder_matches_pinned_sdk_envelope_exactly(
        self,
    ):
        api = self._api()

        reader = (
            api.build_production_live_reader(
                environ=(
                    valid_environment()
                )
            )
        )

        fixture = {
            "fixture": "value",
            "count": 7,
        }

        raw_result = (
            calldata.encode(
                fixture
            ).hex()
        )

        actual = reader._decode_result(
            raw_result=raw_result
        )

        expected = calldata.decode(
            eth_utils.hexadecimal.decode_hex(
                "0x"
                + raw_result
            )
        )

        self.assertEqual(
            actual,
            expected,
        )

        self.assertEqual(
            actual,
            fixture,
        )

    def test_full_simulated_reader_preserves_pinned_block_status_and_receipt_truth(
        self,
    ):
        api = self._api()

        provider = FakeProvider(
            RPC_URL
        )

        expected_contract_result = {
            "protocol": "COMMIT",
            "version": 8,
        }

        encoded_contract_result = (
            calldata.encode(
                expected_contract_result
            ).hex()
        )

        def handler(
            *,
            method,
            params,
        ):
            if method == "gen_call":
                return {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "result": (
                        encoded_contract_result
                    ),
                }

            if (
                method
                == "eth_getTransactionByHash"
            ):
                return {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "result": {
                        "hash": TX_ID,
                        "status": 7,
                        "statusName": (
                            "Finalized"
                        ),
                        "txExecutionResultName": (
                            "FINISHED_WITH_RETURN"
                        ),
                    },
                }

            raise AssertionError(
                method
            )

        provider.handler = handler

        with patch.object(
            api,
            "GenLayerProvider",
            return_value=provider,
        ):
            reader = (
                api.build_production_live_reader(
                    environ=(
                        valid_environment()
                    )
                )
            )

        contract_result = (
            reader.read_contract(
                function_name=(
                    "protocol_info"
                ),
                args=(),
                block_number=123,
                state_status=(
                    "finalized"
                ),
            )
        )

        receipt = (
            reader.get_transaction_receipt(
                genlayer_tx_id=(
                    TX_ID
                )
            )
        )

        self.assertEqual(
            contract_result,
            expected_contract_result,
        )

        self.assertEqual(
            receipt,
            {
                "genlayer_tx_id": (
                    TX_ID
                ),
                "status_code": 7,
                "status_name": (
                    "Finalized"
                ),
                "execution_result": (
                    "FINISHED_WITH_RETURN"
                ),
            },
        )

        self.assertEqual(
            len(
                provider.calls
            ),
            2,
        )

        gen_call = provider.calls[
            0
        ]

        self.assertEqual(
            gen_call[
                "method"
            ],
            "gen_call",
        )

        params = gen_call[
            "params"
        ][
            0
        ]

        self.assertEqual(
            params[
                "blockNumber"
            ],
            hex(
                123
            ),
        )

        self.assertEqual(
            params[
                "status"
            ],
            "finalized",
        )

        self.assertEqual(
            params[
                "to"
            ],
            CONTRACT_ADDRESS,
        )

        self.assertEqual(
            params[
                "from"
            ],
            SENDER_ADDRESS,
        )

        receipt_call = (
            provider.calls[
                1
            ]
        )

        self.assertEqual(
            receipt_call[
                "method"
            ],
            "eth_getTransactionByHash",
        )

        self.assertEqual(
            receipt_call[
                "params"
            ],
            [
                TX_ID,
            ],
        )

    def test_module_has_no_global_environment_database_public_app_polling_or_create_client_coupling(
        self,
    ):
        self._api()

        source = Path(
            "backend/production_live_reader.py"
        ).read_text()

        forbidden = (
            "os.environ",
            "os.getenv",
            "create_client",
            "psycopg",
            "SCHEMA_SQL",
            "DurableStateStore",
            "FastAPI",
            "backend.service_api",
            "backend.production_app",
            "backend.ingestion_runner",
            "requests.",
            "httpx.",
            "time.sleep",
            "asyncio.sleep",
            "wait_for",
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
            "GENLAYER_RPC_URL",
            "COMMIT_CONTRACT_ADDRESS",
            "COMMIT_READER_SENDER_ADDRESS",
            "GenLayerProvider",
            "GenLayerPinnedReader",
            "make_calldata_object",
            "calldata.encode",
            "serialize",
            "calldata.decode",
            "decode_hex",
        )

        for term in required:
            self.assertIn(
                term,
                source,
            )

    def test_public_query_application_remains_disconnected_from_production_live_reader(
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
            "production_live_reader",
            "GenLayerProvider",
            "GenLayerPinnedReader",
            "GENLAYER_RPC_URL",
            "COMMIT_CONTRACT_ADDRESS",
            "COMMIT_READER_SENDER_ADDRESS",
            "gen_getTransactionReceipt",
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
