from __future__ import annotations

from copy import deepcopy
import importlib
import importlib.util
import inspect
from pathlib import Path
import unittest


def _fixture_source_type():
    test_path = Path(
        "tests/test_backend_indexer_contract.py"
    )

    spec = importlib.util.spec_from_file_location(
        "commit_network_adapter_fixture",
        test_path,
    )

    if (
        spec is None
        or spec.loader is None
    ):
        raise RuntimeError(
            "unable to load frozen indexer fixture"
        )

    module = importlib.util.module_from_spec(
        spec
    )

    spec.loader.exec_module(
        module
    )

    return module.FakeCanonicalSource


FakeCanonicalSource = (
    _fixture_source_type()
)


class FakePinnedReader:
    def __init__(self) -> None:
        self.source = FakeCanonicalSource()
        self.calls: list[
            tuple[
                str,
                tuple[object, ...],
                int,
                str,
            ]
        ] = []

    def read_contract(
        self,
        *,
        function_name: str,
        args: tuple[object, ...],
        block_number: int,
        state_status: str,
    ):
        self.calls.append(
            (
                function_name,
                tuple(args),
                block_number,
                state_status,
            )
        )

        if function_name == "protocol_info":
            return deepcopy(
                self.source.protocol
            )

        if function_name == "get_mission_by_index":
            return deepcopy(
                self.source.missions[
                    int(args[0])
                ]
            )

        if function_name == "get_mission_receipt":
            return deepcopy(
                self.source.receipts[
                    str(args[0])
                ]
            )

        if function_name == "get_mission_manifest":
            return deepcopy(
                self.source.manifests[
                    str(args[0])
                ]
            )

        if function_name == "get_effect_by_index":
            return deepcopy(
                self.source.effects[
                    str(args[0])
                ][
                    int(args[1])
                ]
            )

        if function_name == "get_evidence_by_index":
            return deepcopy(
                self.source.evidence[
                    str(args[0])
                ][
                    int(args[1])
                ]
            )

        if function_name == "get_withdrawal_count":
            return len(
                self.source.withdrawals
            )

        if function_name == "get_withdrawal_by_index":
            return deepcopy(
                self.source.withdrawals[
                    int(args[0])
                ]
            )

        raise AssertionError(
            "unexpected read: "
            + function_name
        )


class BackendNetworkAdapterContractTests(
    unittest.TestCase
):
    @staticmethod
    def _api():
        return importlib.import_module(
            "backend.network_adapter"
        )

    def test_public_surface_is_explicit_and_keyword_only(
        self,
    ):
        api = self._api()

        self.assertEqual(
            api.NETWORK_OBSERVATION_SCHEMA,
            "commit-network-index-observation-v1",
        )

        self.assertEqual(
            api.TRANSACTION_OBSERVATION_SCHEMA,
            "commit-network-transaction-observation-v1",
        )

        self.assertEqual(
            api.READ_MODE,
            "PINNED_CANONICAL_READS",
        )

        self.assertEqual(
            api.STATE_ACCEPTED,
            "accepted",
        )

        self.assertEqual(
            api.STATE_FINALIZED,
            "finalized",
        )

        self.assertEqual(
            api.TX_STATUS_ACCEPTED,
            5,
        )

        self.assertEqual(
            api.TX_STATUS_UNDETERMINED,
            6,
        )

        self.assertEqual(
            api.TX_STATUS_FINALIZED,
            7,
        )

        self.assertEqual(
            api.TX_STATUS_VALIDATORS_TIMEOUT,
            11,
        )

        self.assertEqual(
            api.TX_STATUS_LEADER_TIMEOUT,
            12,
        )

        self.assertEqual(
            api.EXECUTION_SUCCESS,
            "FINISHED_WITH_RETURN",
        )

        self.assertTrue(
            issubclass(
                api.NetworkAdapterError,
                ValueError,
            )
        )

        capture_signature = inspect.signature(
            api.build_network_index_observation
        )

        self.assertEqual(
            list(
                capture_signature.parameters
            ),
            [
                "reader",
                "chain_id",
                "contract_address",
                "block_number",
                "state_status",
            ],
        )

        for parameter in (
            capture_signature.parameters.values()
        ):
            self.assertIs(
                parameter.kind,
                inspect.Parameter.KEYWORD_ONLY,
            )

            self.assertIs(
                parameter.default,
                inspect.Parameter.empty,
            )

        tx_signature = inspect.signature(
            api.classify_transaction_observation
        )

        self.assertEqual(
            list(
                tx_signature.parameters
            ),
            [
                "genlayer_tx_id",
                "status_code",
                "status_name",
                "execution_result",
            ],
        )

        for parameter in (
            tx_signature.parameters.values()
        ):
            self.assertIs(
                parameter.kind,
                inspect.Parameter.KEYWORD_ONLY,
            )

            self.assertIs(
                parameter.default,
                inspect.Parameter.empty,
            )

    def test_finalized_reads_are_all_pinned_to_same_block_and_status(
        self,
    ):
        api = self._api()
        reader = FakePinnedReader()

        observation = (
            api.build_network_index_observation(
                reader=reader,
                chain_id=1,
                contract_address=(
                    "0x"
                    + "77" * 20
                ),
                block_number=12345,
                state_status="finalized",
            )
        )

        expected = [
            (
                "protocol_info",
                (),
                12345,
                "finalized",
            ),
            (
                "get_mission_by_index",
                (0,),
                12345,
                "finalized",
            ),
            (
                "get_mission_receipt",
                ("mission-001",),
                12345,
                "finalized",
            ),
            (
                "get_mission_manifest",
                ("mission-001",),
                12345,
                "finalized",
            ),
            (
                "get_effect_by_index",
                (
                    "mission-001",
                    0,
                ),
                12345,
                "finalized",
            ),
            (
                "get_evidence_by_index",
                (
                    "mission-001",
                    0,
                ),
                12345,
                "finalized",
            ),
            (
                "get_evidence_by_index",
                (
                    "mission-001",
                    1,
                ),
                12345,
                "finalized",
            ),
            (
                "get_withdrawal_count",
                (),
                12345,
                "finalized",
            ),
            (
                "get_withdrawal_by_index",
                (0,),
                12345,
                "finalized",
            ),
        ]

        self.assertEqual(
            reader.calls,
            expected,
        )

        self.assertEqual(
            observation[
                "state_basis"
            ],
            "FINALIZED",
        )

        self.assertEqual(
            observation[
                "block_number"
            ],
            12345,
        )

        self.assertEqual(
            observation[
                "state_status"
            ],
            "finalized",
        )

        self.assertEqual(
            observation[
                "index"
            ][
                "finality_status"
            ],
            "UNVERIFIED",
        )

        self.assertEqual(
            observation[
                "index"
            ][
                "execution_status"
            ],
            "UNVERIFIED",
        )

    def test_accepted_state_is_explicitly_provisional(
        self,
    ):
        api = self._api()
        reader = FakePinnedReader()

        observation = (
            api.build_network_index_observation(
                reader=reader,
                chain_id=1,
                contract_address=(
                    "0x"
                    + "77" * 20
                ),
                block_number=12345,
                state_status="accepted",
            )
        )

        self.assertEqual(
            observation[
                "state_basis"
            ],
            "PROVISIONAL",
        )

        self.assertEqual(
            observation[
                "state_status"
            ],
            "accepted",
        )

        self.assertEqual(
            observation[
                "index"
            ][
                "finality_status"
            ],
            "UNVERIFIED",
        )

        self.assertNotEqual(
            observation[
                "state_basis"
            ],
            "FINALIZED",
        )

    def test_block_number_is_required_and_strict_nonnegative_int(
        self,
    ):
        api = self._api()

        for block_number in (
            True,
            -1,
            "123",
            None,
        ):
            with self.subTest(
                block_number=block_number
            ):
                with self.assertRaises(
                    api.NetworkAdapterError
                ):
                    api.build_network_index_observation(
                        reader=FakePinnedReader(),
                        chain_id=1,
                        contract_address=(
                            "0x"
                            + "77" * 20
                        ),
                        block_number=block_number,
                        state_status="finalized",
                    )

    def test_state_status_must_be_exactly_accepted_or_finalized(
        self,
    ):
        api = self._api()

        for state_status in (
            "",
            "latest",
            "FINALIZED",
            "Accepted",
            None,
        ):
            with self.subTest(
                state_status=state_status
            ):
                with self.assertRaises(
                    api.NetworkAdapterError
                ):
                    api.build_network_index_observation(
                        reader=FakePinnedReader(),
                        chain_id=1,
                        contract_address=(
                            "0x"
                            + "77" * 20
                        ),
                        block_number=12345,
                        state_status=state_status,
                    )

    def test_network_identity_must_match_receipt_and_manifest(
        self,
    ):
        api = self._api()

        for field, value in (
            (
                "chain_id",
                999,
            ),
            (
                "contract_address",
                "0x" + "99" * 20,
            ),
        ):
            with self.subTest(
                field=field
            ):
                kwargs = {
                    "reader": FakePinnedReader(),
                    "chain_id": 1,
                    "contract_address": (
                        "0x"
                        + "77" * 20
                    ),
                    "block_number": 12345,
                    "state_status": "finalized",
                }

                kwargs[
                    field
                ] = value

                with self.assertRaises(
                    api.NetworkAdapterError
                ):
                    api.build_network_index_observation(
                        **kwargs
                    )

    def test_accepted_finished_return_is_successful_but_not_final(
        self,
    ):
        api = self._api()

        observation = (
            api.classify_transaction_observation(
                genlayer_tx_id=(
                    "0x"
                    + "ab" * 32
                ),
                status_code=5,
                status_name="Accepted",
                execution_result=(
                    "FINISHED_WITH_RETURN"
                ),
            )
        )

        self.assertTrue(
            observation[
                "successful"
            ]
        )

        self.assertFalse(
            observation[
                "finalized"
            ]
        )

        self.assertFalse(
            observation[
                "final_success"
            ]
        )

        self.assertEqual(
            observation[
                "application_decision"
            ],
            None,
        )

    def test_finalized_finished_return_is_final_success(
        self,
    ):
        api = self._api()

        observation = (
            api.classify_transaction_observation(
                genlayer_tx_id=(
                    "0x"
                    + "ab" * 32
                ),
                status_code=7,
                status_name="Finalized",
                execution_result=(
                    "FINISHED_WITH_RETURN"
                ),
            )
        )

        self.assertTrue(
            observation[
                "successful"
            ]
        )

        self.assertTrue(
            observation[
                "finalized"
            ]
        )

        self.assertTrue(
            observation[
                "final_success"
            ]
        )

        self.assertEqual(
            observation[
                "application_decision"
            ],
            None,
        )

    def test_finalized_execution_error_is_not_success(
        self,
    ):
        api = self._api()

        observation = (
            api.classify_transaction_observation(
                genlayer_tx_id=(
                    "0x"
                    + "ab" * 32
                ),
                status_code=7,
                status_name="Finalized",
                execution_result=(
                    "FINISHED_WITH_ERROR"
                ),
            )
        )

        self.assertFalse(
            observation[
                "successful"
            ]
        )

        self.assertTrue(
            observation[
                "finalized"
            ]
        )

        self.assertFalse(
            observation[
                "final_success"
            ]
        )

    def test_status_code_and_name_must_match(
        self,
    ):
        api = self._api()

        with self.assertRaises(
            api.NetworkAdapterError
        ):
            api.classify_transaction_observation(
                genlayer_tx_id=(
                    "0x"
                    + "ab" * 32
                ),
                status_code=5,
                status_name="Finalized",
                execution_result=(
                    "FINISHED_WITH_RETURN"
                ),
            )

    def test_undetermined_and_timeouts_never_become_application_decisions(
        self,
    ):
        api = self._api()

        cases = (
            (
                6,
                "Undetermined",
            ),
            (
                11,
                "ValidatorsTimeout",
            ),
            (
                12,
                "LeaderTimeout",
            ),
        )

        for status_code, status_name in cases:
            with self.subTest(
                status_code=status_code
            ):
                observation = (
                    api.classify_transaction_observation(
                        genlayer_tx_id=(
                            "0x"
                            + "ab" * 32
                        ),
                        status_code=status_code,
                        status_name=status_name,
                        execution_result="TIMEOUT",
                    )
                )

                self.assertFalse(
                    observation[
                        "successful"
                    ]
                )

                self.assertFalse(
                    observation[
                        "final_success"
                    ]
                )

                self.assertIsNone(
                    observation[
                        "application_decision"
                    ]
                )

    def test_genlayer_transaction_id_is_strict_and_explicit(
        self,
    ):
        api = self._api()

        invalid = (
            "",
            "ab" * 32,
            "0x1234",
            "0x" + "gg" * 32,
            None,
        )

        for genlayer_tx_id in invalid:
            with self.subTest(
                genlayer_tx_id=genlayer_tx_id
            ):
                with self.assertRaises(
                    api.NetworkAdapterError
                ):
                    api.classify_transaction_observation(
                        genlayer_tx_id=genlayer_tx_id,
                        status_code=7,
                        status_name="Finalized",
                        execution_result=(
                            "FINISHED_WITH_RETURN"
                        ),
                    )


if __name__ == "__main__":
    unittest.main()
