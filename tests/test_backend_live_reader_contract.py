from __future__ import annotations

import importlib
import inspect
from pathlib import Path
import unittest


CONTRACT_ADDRESS = (
    "0x"
    + "77" * 20
)

SENDER_ADDRESS = (
    "0x"
    + "88" * 20
)

BLOCK_NUMBER = 123456

TX_ID = (
    "0x"
    + "ab" * 32
)


class LiveReaderContractTests(
    unittest.TestCase
):
    @staticmethod
    def _api():
        return importlib.import_module(
            "backend.live_reader"
        )

    def test_public_surface_and_signatures_are_exact(
        self,
    ):
        api = self._api()

        self.assertEqual(
            api.LIVE_READER_SCHEMA,
            "commit-genlayer-live-reader-v1",
        )

        self.assertTrue(
            issubclass(
                api.LiveReaderError,
                RuntimeError,
            )
        )

        constructor = inspect.signature(
            api.GenLayerPinnedReader
        )

        self.assertEqual(
            list(
                constructor.parameters
            ),
            [
                "make_request",
                "contract_address",
                "sender_address",
                "encode_call",
                "decode_result",
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

        read_signature = inspect.signature(
            api.GenLayerPinnedReader.read_contract
        )

        self.assertEqual(
            list(
                read_signature.parameters
            ),
            [
                "self",
                "function_name",
                "args",
                "block_number",
                "state_status",
            ],
        )

        for name in (
            "function_name",
            "args",
            "block_number",
            "state_status",
        ):
            self.assertIs(
                read_signature.parameters[
                    name
                ].kind,
                inspect.Parameter.KEYWORD_ONLY,
            )

        receipt_signature = (
            inspect.signature(
                api.GenLayerPinnedReader.get_transaction_receipt
            )
        )

        self.assertEqual(
            list(
                receipt_signature.parameters
            ),
            [
                "self",
                "genlayer_tx_id",
            ],
        )

        self.assertIs(
            receipt_signature.parameters[
                "genlayer_tx_id"
            ].kind,
            inspect.Parameter.KEYWORD_ONLY,
        )

    def test_constructor_rejects_invalid_dependencies_and_addresses(
        self,
    ):
        api = self._api()

        valid = {
            "make_request": (
                lambda **kwargs: None
            ),
            "contract_address": (
                CONTRACT_ADDRESS
            ),
            "sender_address": (
                SENDER_ADDRESS
            ),
            "encode_call": (
                lambda **kwargs: "0x01"
            ),
            "decode_result": (
                lambda **kwargs: None
            ),
        }

        cases = (
            (
                "make_request",
                None,
            ),
            (
                "encode_call",
                None,
            ),
            (
                "decode_result",
                None,
            ),
            (
                "contract_address",
                "",
            ),
            (
                "contract_address",
                "not-an-address",
            ),
            (
                "sender_address",
                "",
            ),
            (
                "sender_address",
                "0x1234",
            ),
        )

        for key, value in cases:
            with self.subTest(
                key=key,
                value=repr(
                    value
                ),
            ):
                options = dict(
                    valid
                )

                options[
                    key
                ] = value

                with self.assertRaises(
                    api.LiveReaderError
                ):
                    api.GenLayerPinnedReader(
                        **options
                    )

    def test_gen_call_request_pins_exact_block_and_status(
        self,
    ):
        api = self._api()

        requests = []
        encodes = []
        decodes = []

        def encode_call(
            *,
            function_name,
            args,
        ):
            encodes.append(
                {
                    "function_name": (
                        function_name
                    ),
                    "args": args,
                }
            )

            return "0xfeed"

        def make_request(
            *,
            method,
            params,
        ):
            requests.append(
                {
                    "method": method,
                    "params": params,
                }
            )

            return {
                "jsonrpc": "2.0",
                "result": "cafebabe",
                "id": 1,
            }

        def decode_result(
            *,
            raw_result,
        ):
            decodes.append(
                raw_result
            )

            return {
                "decoded": (
                    raw_result
                ),
            }

        reader = api.GenLayerPinnedReader(
            make_request=make_request,
            contract_address=(
                CONTRACT_ADDRESS
            ),
            sender_address=(
                SENDER_ADDRESS
            ),
            encode_call=encode_call,
            decode_result=decode_result,
        )

        result = reader.read_contract(
            function_name="protocol_info",
            args=(),
            block_number=(
                BLOCK_NUMBER
            ),
            state_status="finalized",
        )

        self.assertEqual(
            encodes,
            [
                {
                    "function_name": (
                        "protocol_info"
                    ),
                    "args": (),
                },
            ],
        )

        self.assertEqual(
            requests,
            [
                {
                    "method": (
                        "gen_call"
                    ),
                    "params": [
                        {
                            "type": "read",
                            "from": (
                                SENDER_ADDRESS
                            ),
                            "to": (
                                CONTRACT_ADDRESS
                            ),
                            "data": (
                                "0xfeed"
                            ),
                            "blockNumber": (
                                hex(
                                    BLOCK_NUMBER
                                )
                            ),
                            "status": (
                                "finalized"
                            ),
                        },
                    ],
                },
            ],
        )

        self.assertEqual(
            decodes,
            [
                "cafebabe",
            ],
        )

        self.assertEqual(
            result,
            {
                "decoded": (
                    "cafebabe"
                ),
            },
        )

    def test_accepted_and_finalized_are_the_only_read_state_statuses(
        self,
    ):
        api = self._api()

        for state_status in (
            "accepted",
            "finalized",
        ):
            with self.subTest(
                state_status=(
                    state_status
                )
            ):
                requests = []

                reader = (
                    api.GenLayerPinnedReader(
                        make_request=(
                            lambda *,
                            method,
                            params: (
                                requests.append(
                                    (
                                        method,
                                        params,
                                    )
                                )
                                or {
                                    "result": (
                                        "00"
                                    )
                                }
                            )
                        ),
                        contract_address=(
                            CONTRACT_ADDRESS
                        ),
                        sender_address=(
                            SENDER_ADDRESS
                        ),
                        encode_call=(
                            lambda **kwargs: (
                                "0x01"
                            )
                        ),
                        decode_result=(
                            lambda **kwargs: (
                                "ok"
                            )
                        ),
                    )
                )

                result = (
                    reader.read_contract(
                        function_name=(
                            "protocol_info"
                        ),
                        args=(),
                        block_number=0,
                        state_status=(
                            state_status
                        ),
                    )
                )

                self.assertEqual(
                    result,
                    "ok",
                )

                self.assertEqual(
                    requests[
                        0
                    ][
                        1
                    ][
                        0
                    ][
                        "status"
                    ],
                    state_status,
                )

    def test_invalid_read_inputs_fail_before_codec_or_rpc(
        self,
    ):
        api = self._api()

        events = []

        def encode_call(
            **kwargs,
        ):
            events.append(
                "encode"
            )

            return "0x01"

        def make_request(
            **kwargs,
        ):
            events.append(
                "rpc"
            )

            return {
                "result": "00",
            }

        reader = api.GenLayerPinnedReader(
            make_request=make_request,
            contract_address=(
                CONTRACT_ADDRESS
            ),
            sender_address=(
                SENDER_ADDRESS
            ),
            encode_call=encode_call,
            decode_result=(
                lambda **kwargs: "ok"
            ),
        )

        cases = (
            {
                "function_name": "",
                "args": (),
                "block_number": 1,
                "state_status": (
                    "finalized"
                ),
            },
            {
                "function_name": (
                    "protocol_info"
                ),
                "args": [],
                "block_number": 1,
                "state_status": (
                    "finalized"
                ),
            },
            {
                "function_name": (
                    "protocol_info"
                ),
                "args": (),
                "block_number": True,
                "state_status": (
                    "finalized"
                ),
            },
            {
                "function_name": (
                    "protocol_info"
                ),
                "args": (),
                "block_number": -1,
                "state_status": (
                    "finalized"
                ),
            },
            {
                "function_name": (
                    "protocol_info"
                ),
                "args": (),
                "block_number": 1,
                "state_status": (
                    "FINALIZED"
                ),
            },
            {
                "function_name": (
                    "protocol_info"
                ),
                "args": (),
                "block_number": 1,
                "state_status": (
                    "latest"
                ),
            },
        )

        for case in cases:
            with self.subTest(
                case=repr(
                    case
                )
            ):
                events.clear()

                with self.assertRaises(
                    api.LiveReaderError
                ):
                    reader.read_contract(
                        **case
                    )

                self.assertEqual(
                    events,
                    [],
                )

    def test_gen_call_rpc_failure_is_sanitized_and_not_retried(
        self,
    ):
        api = self._api()

        calls = []

        def make_request(
            **kwargs,
        ):
            calls.append(
                kwargs
            )

            raise RuntimeError(
                "secret rpc detail"
            )

        reader = api.GenLayerPinnedReader(
            make_request=make_request,
            contract_address=(
                CONTRACT_ADDRESS
            ),
            sender_address=(
                SENDER_ADDRESS
            ),
            encode_call=(
                lambda **kwargs: (
                    "0x01"
                )
            ),
            decode_result=(
                lambda **kwargs: (
                    "unreachable"
                )
            ),
        )

        try:
            reader.read_contract(
                function_name=(
                    "protocol_info"
                ),
                args=(),
                block_number=1,
                state_status="accepted",
            )
        except api.LiveReaderError as exc:
            rendered = str(
                exc
            ).lower()
        else:
            self.fail(
                "RPC failure was silently accepted"
            )

        self.assertEqual(
            len(
                calls
            ),
            1,
        )

        self.assertNotIn(
            "secret",
            rendered,
        )

        self.assertNotIn(
            "rpc detail",
            rendered,
        )

    def test_malformed_gen_call_response_fails_closed_before_decode(
        self,
    ):
        api = self._api()

        malformed = (
            None,
            {},
            {
                "result": None,
            },
            {
                "result": 123,
            },
        )

        for response in malformed:
            with self.subTest(
                response=repr(
                    response
                )
            ):
                decodes = []

                reader = (
                    api.GenLayerPinnedReader(
                        make_request=(
                            lambda **kwargs: (
                                response
                            )
                        ),
                        contract_address=(
                            CONTRACT_ADDRESS
                        ),
                        sender_address=(
                            SENDER_ADDRESS
                        ),
                        encode_call=(
                            lambda **kwargs: (
                                "0x01"
                            )
                        ),
                        decode_result=(
                            lambda **kwargs: (
                                decodes.append(
                                    kwargs
                                )
                            )
                        ),
                    )
                )

                with self.assertRaises(
                    api.LiveReaderError
                ):
                    reader.read_contract(
                        function_name=(
                            "protocol_info"
                        ),
                        args=(),
                        block_number=1,
                        state_status=(
                            "finalized"
                        ),
                    )

                self.assertEqual(
                    decodes,
                    [],
                )

    def test_decode_failure_is_sanitized(
        self,
    ):
        api = self._api()

        reader = api.GenLayerPinnedReader(
            make_request=(
                lambda **kwargs: {
                    "result": "00",
                }
            ),
            contract_address=(
                CONTRACT_ADDRESS
            ),
            sender_address=(
                SENDER_ADDRESS
            ),
            encode_call=(
                lambda **kwargs: (
                    "0x01"
                )
            ),
            decode_result=(
                lambda **kwargs: (
                    (_ for _ in ()).throw(
                        ValueError(
                            "secret decode detail"
                        )
                    )
                )
            ),
        )

        try:
            reader.read_contract(
                function_name=(
                    "protocol_info"
                ),
                args=(),
                block_number=1,
                state_status=(
                    "finalized"
                ),
            )
        except api.LiveReaderError as exc:
            rendered = str(
                exc
            ).lower()
        else:
            self.fail(
                "decode failure was silently accepted"
            )

        self.assertNotIn(
            "secret",
            rendered,
        )

        self.assertNotIn(
            "decode detail",
            rendered,
        )

    def test_transaction_receipt_rpc_request_and_normalization_are_exact(
        self,
    ):
        api = self._api()

        requests = []

        receipt = {
            "id": TX_ID,
            "status": 7,
            "statusName": (
                "Finalized"
            ),
            "txExecutionResultName": (
                "FINISHED_WITH_RETURN"
            ),
        }

        def make_request(
            *,
            method,
            params,
        ):
            requests.append(
                {
                    "method": method,
                    "params": params,
                }
            )

            return {
                "jsonrpc": "2.0",
                "result": receipt,
                "id": 1,
            }

        reader = api.GenLayerPinnedReader(
            make_request=make_request,
            contract_address=(
                CONTRACT_ADDRESS
            ),
            sender_address=(
                SENDER_ADDRESS
            ),
            encode_call=(
                lambda **kwargs: (
                    "0x01"
                )
            ),
            decode_result=(
                lambda **kwargs: (
                    None
                )
            ),
        )

        result = (
            reader.get_transaction_receipt(
                genlayer_tx_id=(
                    TX_ID
                )
            )
        )

        self.assertEqual(
            requests,
            [
                {
                    "method": (
                        "gen_getTransactionReceipt"
                    ),
                    "params": [
                        {
                            "txId": (
                                TX_ID
                            ),
                        },
                    ],
                },
            ],
        )

        self.assertEqual(
            result,
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

    def test_transaction_receipt_id_mismatch_fails_closed(
        self,
    ):
        api = self._api()

        reader = api.GenLayerPinnedReader(
            make_request=(
                lambda **kwargs: {
                    "result": {
                        "id": (
                            "0x"
                            + "cd" * 32
                        ),
                        "status": 7,
                        "statusName": (
                            "Finalized"
                        ),
                        "txExecutionResultName": (
                            "FINISHED_WITH_RETURN"
                        ),
                    },
                }
            ),
            contract_address=(
                CONTRACT_ADDRESS
            ),
            sender_address=(
                SENDER_ADDRESS
            ),
            encode_call=(
                lambda **kwargs: (
                    "0x01"
                )
            ),
            decode_result=(
                lambda **kwargs: (
                    None
                )
            ),
        )

        with self.assertRaises(
            api.LiveReaderError
        ):
            reader.get_transaction_receipt(
                genlayer_tx_id=(
                    TX_ID
                )
            )

    def test_malformed_transaction_receipt_fails_closed(
        self,
    ):
        api = self._api()

        malformed_receipts = (
            None,
            {},
            {
                "id": TX_ID,
                "status": True,
                "statusName": (
                    "Finalized"
                ),
                "txExecutionResultName": (
                    "FINISHED_WITH_RETURN"
                ),
            },
            {
                "id": TX_ID,
                "status": 7,
                "statusName": "",
                "txExecutionResultName": (
                    "FINISHED_WITH_RETURN"
                ),
            },
            {
                "id": TX_ID,
                "status": 7,
                "statusName": (
                    "Finalized"
                ),
                "txExecutionResultName": "",
            },
        )

        for receipt in malformed_receipts:
            with self.subTest(
                receipt=repr(
                    receipt
                )
            ):
                reader = (
                    api.GenLayerPinnedReader(
                        make_request=(
                            lambda **kwargs: {
                                "result": receipt,
                            }
                        ),
                        contract_address=(
                            CONTRACT_ADDRESS
                        ),
                        sender_address=(
                            SENDER_ADDRESS
                        ),
                        encode_call=(
                            lambda **kwargs: (
                                "0x01"
                            )
                        ),
                        decode_result=(
                            lambda **kwargs: (
                                None
                            )
                        ),
                    )
                )

                with self.assertRaises(
                    api.LiveReaderError
                ):
                    reader.get_transaction_receipt(
                        genlayer_tx_id=(
                            TX_ID
                        )
                    )

    def test_transaction_receipt_does_not_synthesize_success_finality_or_application_decision(
        self,
    ):
        api = self._api()

        receipt = {
            "id": TX_ID,
            "status": 5,
            "statusName": (
                "Accepted"
            ),
            "txExecutionResultName": (
                "FAILED"
            ),
            "result": "irrelevant",
            "applicationDecision": (
                "YES"
            ),
        }

        reader = api.GenLayerPinnedReader(
            make_request=(
                lambda **kwargs: {
                    "result": receipt,
                }
            ),
            contract_address=(
                CONTRACT_ADDRESS
            ),
            sender_address=(
                SENDER_ADDRESS
            ),
            encode_call=(
                lambda **kwargs: (
                    "0x01"
                )
            ),
            decode_result=(
                lambda **kwargs: (
                    None
                )
            ),
        )

        result = (
            reader.get_transaction_receipt(
                genlayer_tx_id=(
                    TX_ID
                )
            )
        )

        self.assertEqual(
            result,
            {
                "genlayer_tx_id": (
                    TX_ID
                ),
                "status_code": 5,
                "status_name": (
                    "Accepted"
                ),
                "execution_result": (
                    "FAILED"
                ),
            },
        )

        self.assertNotIn(
            "successful",
            result,
        )

        self.assertNotIn(
            "finalized",
            result,
        )

        self.assertNotIn(
            "final_success",
            result,
        )

        self.assertNotIn(
            "application_decision",
            result,
        )

    def test_library_has_no_environment_http_database_storage_polling_or_public_app_coupling(
        self,
    ):
        self._api()

        source = Path(
            "backend/live_reader.py"
        ).read_text()

        forbidden = (
            "os.environ",
            "os.getenv",
            "requests.",
            "httpx.",
            "urllib.",
            "psycopg",
            "SCHEMA_SQL",
            "DurableStateStore",
            "FastAPI",
            "backend.service_api",
            "backend.production_app",
            "backend.ingestion_runner",
            "time.sleep",
            "asyncio.sleep",
            "wait_for",
            "gen_getTransactionStatus",
            "application_decision",
        )

        for term in forbidden:
            self.assertNotIn(
                term,
                source,
            )

        required = (
            "gen_call",
            "gen_getTransactionReceipt",
            "blockNumber",
            "status",
            "statusName",
            "txExecutionResultName",
        )

        for term in required:
            self.assertIn(
                term,
                source,
            )

    def test_rpc_failures_have_no_hidden_retry(
        self,
    ):
        api = self._api()

        calls = []

        def make_request(
            **kwargs,
        ):
            calls.append(
                kwargs
            )

            raise RuntimeError(
                "private transport failure"
            )

        reader = api.GenLayerPinnedReader(
            make_request=make_request,
            contract_address=(
                CONTRACT_ADDRESS
            ),
            sender_address=(
                SENDER_ADDRESS
            ),
            encode_call=(
                lambda **kwargs: (
                    "0x01"
                )
            ),
            decode_result=(
                lambda **kwargs: (
                    None
                )
            ),
        )

        for operation in (
            lambda: reader.read_contract(
                function_name=(
                    "protocol_info"
                ),
                args=(),
                block_number=1,
                state_status=(
                    "accepted"
                ),
            ),
            lambda: (
                reader.get_transaction_receipt(
                    genlayer_tx_id=(
                        TX_ID
                    )
                )
            ),
        ):
            before = len(
                calls
            )

            with self.assertRaises(
                api.LiveReaderError
            ):
                operation()

            self.assertEqual(
                len(
                    calls
                ),
                before + 1,
            )


if __name__ == "__main__":
    unittest.main()
