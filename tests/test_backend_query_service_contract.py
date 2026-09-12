from __future__ import annotations

from copy import deepcopy
import importlib
import importlib.util
import inspect
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


def _fixture_module():
    file_name = Path(
        "tests/test_backend_network_adapter_contract.py"
    )

    spec = importlib.util.spec_from_file_location(
        "commit_query_service_fixture",
        file_name,
    )

    if (
        spec is None
        or spec.loader is None
    ):
        raise RuntimeError(
            "unable to load network fixture"
        )

    module = importlib.util.module_from_spec(
        spec
    )

    spec.loader.exec_module(
        module
    )

    return module


FIXTURE = _fixture_module()
FakePinnedReader = FIXTURE.FakePinnedReader

CHAIN_ID = 1
CONTRACT_ADDRESS = (
    "0x"
    + "77" * 20
)

TX_ID = (
    "0x"
    + "ab" * 32
)


def _index_observation(
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

    return build_network_index_observation(
        reader=reader,
        chain_id=CHAIN_ID,
        contract_address=(
            CONTRACT_ADDRESS
        ),
        block_number=block_number,
        state_status=state_status,
    )


def _state_with_indexes(
    *observations,
):
    state = (
        empty_persistence_state()
    )

    for observation in observations:
        state = (
            apply_index_observation(
                state=state,
                observation=observation,
            )
        )

    return state


def _transaction_observation(
    *,
    status_code: int = 7,
    status_name: str = "Finalized",
    execution_result: str = (
        "FINISHED_WITH_RETURN"
    ),
):
    return classify_transaction_observation(
        genlayer_tx_id=TX_ID,
        status_code=status_code,
        status_name=status_name,
        execution_result=execution_result,
    )


class BackendQueryServiceContractTests(
    unittest.TestCase
):
    @staticmethod
    def _api():
        return importlib.import_module(
            "backend.query_service"
        )

    def test_public_surface_is_versioned_and_keyword_only(
        self,
    ):
        api = self._api()

        self.assertEqual(
            api.INDEX_QUERY_SCHEMA,
            "commit-backend-index-query-v1",
        )

        self.assertEqual(
            api.TRANSACTION_QUERY_SCHEMA,
            "commit-backend-transaction-query-v1",
        )

        self.assertEqual(
            api.STATE_BASIS_FINALIZED,
            "FINALIZED",
        )

        self.assertEqual(
            api.STATE_BASIS_PROVISIONAL,
            "PROVISIONAL",
        )

        self.assertTrue(
            issubclass(
                api.QueryServiceError,
                ValueError,
            )
        )

        index_signature = (
            inspect.signature(
                api.build_index_query_view
            )
        )

        self.assertEqual(
            list(
                index_signature.parameters
            ),
            [
                "state",
                "chain_id",
                "contract_address",
                "state_basis",
            ],
        )

        for parameter in (
            index_signature.parameters.values()
        ):
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
                api.build_transaction_query_view
            )
        )

        self.assertEqual(
            list(
                transaction_signature.parameters
            ),
            [
                "state",
                "genlayer_tx_id",
            ],
        )

        for parameter in (
            transaction_signature.parameters.values()
        ):
            self.assertIs(
                parameter.kind,
                inspect.Parameter.KEYWORD_ONLY,
            )

            self.assertIs(
                parameter.default,
                inspect.Parameter.empty,
            )

    def test_latest_finalized_selects_highest_numeric_block(
        self,
    ):
        api = self._api()

        state = _state_with_indexes(
            _index_observation(
                block_number=11,
                state_status="finalized",
            ),
            _index_observation(
                block_number=13,
                state_status="accepted",
            ),
            _index_observation(
                block_number=12,
                state_status="finalized",
            ),
        )

        view = (
            api.build_index_query_view(
                state=state,
                chain_id=CHAIN_ID,
                contract_address=(
                    CONTRACT_ADDRESS
                ),
                state_basis="FINALIZED",
            )
        )

        self.assertEqual(
            set(
                view
            ),
            {
                "schema",
                "found",
                "chain_id",
                "contract_address",
                "requested_state_basis",
                "source_record_key",
                "source_payload_digest",
                "block_number",
                "state_status",
                "state_basis",
                "network_identity_verified",
                "network_identity_basis",
                "protocol",
                "missions",
                "withdrawals",
            },
        )

        self.assertEqual(
            view[
                "schema"
            ],
            api.INDEX_QUERY_SCHEMA,
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
            12,
        )

        self.assertEqual(
            view[
                "state_status"
            ],
            "finalized",
        )

        self.assertEqual(
            view[
                "state_basis"
            ],
            "FINALIZED",
        )

        self.assertEqual(
            view[
                "requested_state_basis"
            ],
            "FINALIZED",
        )

    def test_latest_provisional_selects_highest_numeric_block(
        self,
    ):
        api = self._api()

        state = _state_with_indexes(
            _index_observation(
                block_number=12,
                state_status="finalized",
            ),
            _index_observation(
                block_number=13,
                state_status="accepted",
            ),
            _index_observation(
                block_number=14,
                state_status="accepted",
            ),
        )

        view = (
            api.build_index_query_view(
                state=state,
                chain_id=CHAIN_ID,
                contract_address=(
                    CONTRACT_ADDRESS
                ),
                state_basis="PROVISIONAL",
            )
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
            14,
        )

        self.assertEqual(
            view[
                "state_basis"
            ],
            "PROVISIONAL",
        )

    def test_finalized_query_never_falls_back_to_provisional(
        self,
    ):
        api = self._api()

        state = _state_with_indexes(
            _index_observation(
                block_number=20,
                state_status="accepted",
            )
        )

        view = (
            api.build_index_query_view(
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
                "found"
            ],
            False,
        )

        self.assertEqual(
            view[
                "requested_state_basis"
            ],
            "FINALIZED",
        )

        self.assertIsNone(
            view[
                "source_record_key"
            ]
        )

        self.assertIsNone(
            view[
                "source_payload_digest"
            ]
        )

        self.assertIsNone(
            view[
                "block_number"
            ]
        )

        self.assertIsNone(
            view[
                "state_status"
            ]
        )

        self.assertIsNone(
            view[
                "state_basis"
            ]
        )

        self.assertEqual(
            view[
                "missions"
            ],
            [],
        )

        self.assertEqual(
            view[
                "withdrawals"
            ],
            [],
        )

    def test_provisional_query_never_falls_back_to_finalized(
        self,
    ):
        api = self._api()

        state = _state_with_indexes(
            _index_observation(
                block_number=20,
                state_status="finalized",
            )
        )

        view = (
            api.build_index_query_view(
                state=state,
                chain_id=CHAIN_ID,
                contract_address=(
                    CONTRACT_ADDRESS
                ),
                state_basis="PROVISIONAL",
            )
        )

        self.assertIs(
            view[
                "found"
            ],
            False,
        )

        self.assertEqual(
            view[
                "requested_state_basis"
            ],
            "PROVISIONAL",
        )

    def test_network_identity_nonclaim_is_preserved(
        self,
    ):
        api = self._api()

        state = _state_with_indexes(
            _index_observation(
                block_number=30,
                state_status="finalized",
                mission_count=0,
            )
        )

        view = (
            api.build_index_query_view(
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
                "found"
            ],
            True,
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

        self.assertEqual(
            view[
                "missions"
            ],
            [],
        )

    def test_index_query_preserves_source_record_and_digest(
        self,
    ):
        api = self._api()

        state = _state_with_indexes(
            _index_observation(
                block_number=44,
                state_status="finalized",
            )
        )

        record_key = (
            str(
                CHAIN_ID
            )
            + ":"
            + CONTRACT_ADDRESS.lower()
            + ":44"
        )

        persisted_record = (
            state[
                "index_records"
            ][
                record_key
            ]
        )

        view = (
            api.build_index_query_view(
                state=state,
                chain_id=CHAIN_ID,
                contract_address=(
                    CONTRACT_ADDRESS
                ),
                state_basis="FINALIZED",
            )
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
            persisted_record[
                "payload_digest"
            ],
        )

    def test_index_query_result_is_deeply_detached(
        self,
    ):
        api = self._api()

        state = _state_with_indexes(
            _index_observation(
                block_number=50,
                state_status="finalized",
            )
        )

        state_before = deepcopy(
            state
        )

        view = (
            api.build_index_query_view(
                state=state,
                chain_id=CHAIN_ID,
                contract_address=(
                    CONTRACT_ADDRESS
                ),
                state_basis="FINALIZED",
            )
        )

        view[
            "protocol"
        ][
            "revision"
        ] = "query-result-mutation"

        view[
            "missions"
        ].clear()

        view[
            "withdrawals"
        ].clear()

        self.assertEqual(
            state,
            state_before,
        )

    def test_invalid_persistence_state_is_rejected_before_query(
        self,
    ):
        api = self._api()

        state = _state_with_indexes(
            _index_observation(
                block_number=60,
                state_status="finalized",
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
            api.QueryServiceError
        ):
            api.build_index_query_view(
                state=forged,
                chain_id=CHAIN_ID,
                contract_address=(
                    CONTRACT_ADDRESS
                ),
                state_basis="FINALIZED",
            )

    def test_index_query_inputs_are_strict(
        self,
    ):
        api = self._api()

        state = (
            empty_persistence_state()
        )

        invalid_inputs = (
            {
                "chain_id": True,
                "contract_address": (
                    CONTRACT_ADDRESS
                ),
                "state_basis": "FINALIZED",
            },
            {
                "chain_id": 0,
                "contract_address": (
                    CONTRACT_ADDRESS
                ),
                "state_basis": "FINALIZED",
            },
            {
                "chain_id": CHAIN_ID,
                "contract_address": "not-an-address",
                "state_basis": "FINALIZED",
            },
            {
                "chain_id": CHAIN_ID,
                "contract_address": (
                    "0x"
                    + "00" * 20
                ),
                "state_basis": "FINALIZED",
            },
            {
                "chain_id": CHAIN_ID,
                "contract_address": (
                    CONTRACT_ADDRESS
                ),
                "state_basis": "finalized",
            },
            {
                "chain_id": CHAIN_ID,
                "contract_address": (
                    CONTRACT_ADDRESS
                ),
                "state_basis": "LATEST",
            },
        )

        for case in invalid_inputs:
            with self.assertRaises(
                api.QueryServiceError
            ):
                api.build_index_query_view(
                    state=state,
                    **case,
                )

    def test_transaction_query_is_exact_and_provenance_bound(
        self,
    ):
        api = self._api()

        transaction = (
            _transaction_observation()
        )

        state = (
            apply_transaction_observation(
                state=(
                    empty_persistence_state()
                ),
                observation=transaction,
            )
        )

        persisted_record = (
            state[
                "transaction_records"
            ][
                TX_ID
            ]
        )

        view = (
            api.build_transaction_query_view(
                state=state,
                genlayer_tx_id=TX_ID,
            )
        )

        self.assertEqual(
            set(
                view
            ),
            {
                "schema",
                "found",
                "genlayer_tx_id",
                "source_record_key",
                "source_payload_digest",
                "status_code",
                "status_name",
                "execution_result",
                "successful",
                "finalized",
                "final_success",
                "application_decision",
            },
        )

        self.assertEqual(
            view[
                "schema"
            ],
            api.TRANSACTION_QUERY_SCHEMA,
        )

        self.assertIs(
            view[
                "found"
            ],
            True,
        )

        self.assertEqual(
            view[
                "source_record_key"
            ],
            TX_ID,
        )

        self.assertEqual(
            view[
                "source_payload_digest"
            ],
            persisted_record[
                "payload_digest"
            ],
        )

        self.assertEqual(
            view[
                "status_code"
            ],
            7,
        )

        self.assertEqual(
            view[
                "status_name"
            ],
            "Finalized",
        )

        self.assertIs(
            view[
                "final_success"
            ],
            True,
        )

    def test_missing_transaction_is_explicit_not_found(
        self,
    ):
        api = self._api()

        view = (
            api.build_transaction_query_view(
                state=(
                    empty_persistence_state()
                ),
                genlayer_tx_id=TX_ID,
            )
        )

        self.assertIs(
            view[
                "found"
            ],
            False,
        )

        self.assertEqual(
            view[
                "genlayer_tx_id"
            ],
            TX_ID,
        )

        self.assertIsNone(
            view[
                "source_record_key"
            ]
        )

        self.assertIsNone(
            view[
                "source_payload_digest"
            ]
        )

        self.assertIsNone(
            view[
                "status_code"
            ]
        )

        self.assertIsNone(
            view[
                "finalized"
            ]
        )

        self.assertIsNone(
            view[
                "final_success"
            ]
        )

        self.assertIsNone(
            view[
                "application_decision"
            ]
        )

    def test_transaction_query_never_synthesizes_application_decision(
        self,
    ):
        api = self._api()

        state = (
            apply_transaction_observation(
                state=(
                    empty_persistence_state()
                ),
                observation=(
                    _transaction_observation(
                        status_code=6,
                        status_name="Undetermined",
                        execution_result="TIMEOUT",
                    )
                ),
            )
        )

        view = (
            api.build_transaction_query_view(
                state=state,
                genlayer_tx_id=TX_ID,
            )
        )

        self.assertIs(
            view[
                "found"
            ],
            True,
        )

        self.assertEqual(
            view[
                "status_name"
            ],
            "Undetermined",
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

    def test_transaction_query_result_is_deeply_detached(
        self,
    ):
        api = self._api()

        state = (
            apply_transaction_observation(
                state=(
                    empty_persistence_state()
                ),
                observation=(
                    _transaction_observation()
                ),
            )
        )

        state_before = deepcopy(
            state
        )

        view = (
            api.build_transaction_query_view(
                state=state,
                genlayer_tx_id=TX_ID,
            )
        )

        view[
            "status_name"
        ] = "Tampered"

        view[
            "source_payload_digest"
        ] = (
            "0"
            * 64
        )

        self.assertEqual(
            state,
            state_before,
        )


if __name__ == "__main__":
    unittest.main()
