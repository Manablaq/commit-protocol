from __future__ import annotations

from copy import deepcopy
import importlib.util
from pathlib import Path
import unittest

from backend.network_adapter import (
    build_network_index_observation,
    classify_transaction_observation,
)
from backend.persistence import (
    apply_index_observation,
    apply_transaction_observation,
    empty_persistence_state,
)
from backend.query_service import (
    QueryServiceError,
    build_index_query_view,
    build_transaction_query_view,
    validate_index_query_view,
    validate_transaction_query_view,
)


CHAIN_ID = 1
CONTRACT_ADDRESS = (
    "0x"
    + "77" * 20
)
TX_ID = (
    "0x"
    + "ab" * 32
)


def _fixture_module():
    file_name = Path(
        "tests/test_backend_network_adapter_contract.py"
    )

    spec = importlib.util.spec_from_file_location(
        "commit_backend_integration_fixture",
        file_name,
    )

    if (
        spec is None
        or spec.loader is None
    ):
        raise RuntimeError(
            "unable to load backend fixture"
        )

    module = importlib.util.module_from_spec(
        spec
    )

    spec.loader.exec_module(
        module
    )

    return module


FIXTURE = _fixture_module()
FakePinnedReader = (
    FIXTURE.FakePinnedReader
)


def _network_observation(
    *,
    block_number: int,
    state_status: str,
    mission_count: int | None = None,
):
    reader = FakePinnedReader()

    if mission_count is not None:
        reader.source.protocol[
            "mission_count"
        ] = mission_count

    observation = (
        build_network_index_observation(
            reader=reader,
            chain_id=CHAIN_ID,
            contract_address=(
                CONTRACT_ADDRESS
            ),
            block_number=block_number,
            state_status=state_status,
        )
    )

    return (
        observation,
        reader,
    )


class BackendIntegrationGateTests(
    unittest.TestCase
):
    def test_pinned_finalized_network_observation_flows_to_query(
        self,
    ):
        observation, reader = (
            _network_observation(
                block_number=100,
                state_status="finalized",
            )
        )

        state = (
            apply_index_observation(
                state=(
                    empty_persistence_state()
                ),
                observation=observation,
            )
        )

        view = build_index_query_view(
            state=state,
            chain_id=CHAIN_ID,
            contract_address=(
                CONTRACT_ADDRESS
            ),
            state_basis="FINALIZED",
        )

        self.assertIs(
            view[
                "found"
            ],
            True,
        )

        self.assertEqual(
            view[
                "block_number"
            ],
            100,
        )

        self.assertEqual(
            view[
                "state_basis"
            ],
            "FINALIZED",
        )

        self.assertIs(
            validate_index_query_view(
                view
            ),
            view,
        )

        record_key = (
            "1:"
            + CONTRACT_ADDRESS.lower()
            + ":100"
        )

        self.assertEqual(
            view[
                "source_record_key"
            ],
            record_key,
        )

        self.assertEqual(
            view[
                "source_payload_digest"
            ],
            state[
                "index_records"
            ][
                record_key
            ][
                "payload_digest"
            ],
        )

        self.assertGreater(
            len(
                reader.calls
            ),
            0,
        )

    def test_every_canonical_read_is_pinned_to_same_boundary(
        self,
    ):
        _observation, reader = (
            _network_observation(
                block_number=321,
                state_status="finalized",
            )
        )

        expected_names = [
            "protocol_info",
            "get_mission_by_index",
            "get_mission_receipt",
            "get_mission_manifest",
            "get_effect_by_index",
            "get_evidence_by_index",
            "get_evidence_by_index",
            "get_withdrawal_count",
            "get_withdrawal_by_index",
        ]

        self.assertEqual(
            [
                call[
                    0
                ]
                for call in reader.calls
            ],
            expected_names,
        )

        for call in reader.calls:
            self.assertEqual(
                call[
                    2
                ],
                321,
            )

            self.assertEqual(
                call[
                    3
                ],
                "finalized",
            )

    def test_index_accepted_to_finalized_promotion_is_end_to_end(
        self,
    ):
        accepted, _ = (
            _network_observation(
                block_number=400,
                state_status="accepted",
            )
        )

        finalized, _ = (
            _network_observation(
                block_number=400,
                state_status="finalized",
            )
        )

        state = (
            apply_index_observation(
                state=(
                    empty_persistence_state()
                ),
                observation=accepted,
            )
        )

        provisional_view = (
            build_index_query_view(
                state=state,
                chain_id=CHAIN_ID,
                contract_address=(
                    CONTRACT_ADDRESS
                ),
                state_basis="PROVISIONAL",
            )
        )

        self.assertIs(
            provisional_view[
                "found"
            ],
            True,
        )

        state = (
            apply_index_observation(
                state=state,
                observation=finalized,
            )
        )

        finalized_view = (
            build_index_query_view(
                state=state,
                chain_id=CHAIN_ID,
                contract_address=(
                    CONTRACT_ADDRESS
                ),
                state_basis="FINALIZED",
            )
        )

        provisional_after = (
            build_index_query_view(
                state=state,
                chain_id=CHAIN_ID,
                contract_address=(
                    CONTRACT_ADDRESS
                ),
                state_basis="PROVISIONAL",
            )
        )

        self.assertIs(
            finalized_view[
                "found"
            ],
            True,
        )

        self.assertIs(
            provisional_after[
                "found"
            ],
            False,
        )

    def test_transaction_accepted_to_finalized_promotion_is_end_to_end(
        self,
    ):
        accepted = (
            classify_transaction_observation(
                genlayer_tx_id=TX_ID,
                status_code=5,
                status_name="Accepted",
                execution_result=(
                    "FINISHED_WITH_RETURN"
                ),
            )
        )

        finalized = (
            classify_transaction_observation(
                genlayer_tx_id=TX_ID,
                status_code=7,
                status_name="Finalized",
                execution_result=(
                    "FINISHED_WITH_RETURN"
                ),
            )
        )

        state = (
            apply_transaction_observation(
                state=(
                    empty_persistence_state()
                ),
                observation=accepted,
            )
        )

        accepted_view = (
            build_transaction_query_view(
                state=state,
                genlayer_tx_id=TX_ID,
            )
        )

        self.assertIs(
            accepted_view[
                "successful"
            ],
            True,
        )

        self.assertIs(
            accepted_view[
                "finalized"
            ],
            False,
        )

        self.assertIs(
            accepted_view[
                "final_success"
            ],
            False,
        )

        state = (
            apply_transaction_observation(
                state=state,
                observation=finalized,
            )
        )

        finalized_view = (
            build_transaction_query_view(
                state=state,
                genlayer_tx_id=TX_ID,
            )
        )

        self.assertIs(
            finalized_view[
                "successful"
            ],
            True,
        )

        self.assertIs(
            finalized_view[
                "finalized"
            ],
            True,
        )

        self.assertIs(
            finalized_view[
                "final_success"
            ],
            True,
        )

        self.assertIsNone(
            finalized_view[
                "application_decision"
            ]
        )

        self.assertIs(
            validate_transaction_query_view(
                finalized_view
            ),
            finalized_view,
        )

    def test_finalized_execution_error_never_becomes_success(
        self,
    ):
        observation = (
            classify_transaction_observation(
                genlayer_tx_id=TX_ID,
                status_code=7,
                status_name="Finalized",
                execution_result=(
                    "FINISHED_WITH_ERROR"
                ),
            )
        )

        state = (
            apply_transaction_observation(
                state=(
                    empty_persistence_state()
                ),
                observation=observation,
            )
        )

        view = (
            build_transaction_query_view(
                state=state,
                genlayer_tx_id=TX_ID,
            )
        )

        self.assertIs(
            view[
                "successful"
            ],
            False,
        )

        self.assertIs(
            view[
                "finalized"
            ],
            True,
        )

        self.assertIs(
            view[
                "final_success"
            ],
            False,
        )

        self.assertIsNone(
            view[
                "application_decision"
            ]
        )

    def test_empty_mission_identity_nonclaim_survives_full_pipeline(
        self,
    ):
        observation, _ = (
            _network_observation(
                block_number=500,
                state_status="finalized",
                mission_count=0,
            )
        )

        self.assertIs(
            observation[
                "network_identity_verified"
            ],
            False,
        )

        self.assertEqual(
            observation[
                "network_identity_basis"
            ],
            "UNVERIFIED_NO_MISSIONS",
        )

        state = (
            apply_index_observation(
                state=(
                    empty_persistence_state()
                ),
                observation=observation,
            )
        )

        view = (
            build_index_query_view(
                state=state,
                chain_id=CHAIN_ID,
                contract_address=(
                    CONTRACT_ADDRESS
                ),
                state_basis="FINALIZED",
            )
        )

        self.assertIs(
            view[
                "network_identity_verified"
            ],
            False,
        )

        self.assertEqual(
            view[
                "network_identity_basis"
            ],
            "UNVERIFIED_NO_MISSIONS",
        )

    def test_tampered_persistence_is_rejected_before_query_projection(
        self,
    ):
        observation, _ = (
            _network_observation(
                block_number=600,
                state_status="finalized",
            )
        )

        state = (
            apply_index_observation(
                state=(
                    empty_persistence_state()
                ),
                observation=observation,
            )
        )

        forged = deepcopy(
            state
        )

        record = next(
            iter(
                forged[
                    "index_records"
                ].values()
            )
        )

        record[
            "payload_digest"
        ] = (
            "0"
            * 64
        )

        with self.assertRaises(
            QueryServiceError
        ):
            build_index_query_view(
                state=forged,
                chain_id=CHAIN_ID,
                contract_address=(
                    CONTRACT_ADDRESS
                ),
                state_basis="FINALIZED",
            )

    def test_protocol_timeout_or_undetermined_never_becomes_app_decision(
        self,
    ):
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

        for (
            status_code,
            status_name,
        ) in cases:
            with self.subTest(
                status_name=status_name
            ):
                observation = (
                    classify_transaction_observation(
                        genlayer_tx_id=TX_ID,
                        status_code=status_code,
                        status_name=status_name,
                        execution_result="TIMEOUT",
                    )
                )

                state = (
                    apply_transaction_observation(
                        state=(
                            empty_persistence_state()
                        ),
                        observation=observation,
                    )
                )

                view = (
                    build_transaction_query_view(
                        state=state,
                        genlayer_tx_id=TX_ID,
                    )
                )

                self.assertIsNone(
                    view[
                        "application_decision"
                    ]
                )

                self.assertIs(
                    view[
                        "final_success"
                    ],
                    False,
                )


if __name__ == "__main__":
    unittest.main()
