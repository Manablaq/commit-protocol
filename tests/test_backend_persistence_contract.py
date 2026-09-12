from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib
import importlib.util
import inspect
import json
from pathlib import Path
import unittest

from backend.network_adapter import (
    NetworkAdapterError,
    build_network_index_observation,
    classify_transaction_observation,
)


def _fixture_module():
    file_name = Path(
        "tests/test_backend_network_adapter_contract.py"
    )

    spec = importlib.util.spec_from_file_location(
        "commit_persistence_fixture",
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


def _canonical_digest(
    value: object,
) -> str:
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(
            ",",
            ":",
        ),
        ensure_ascii=False,
    ).encode(
        "utf-8"
    )

    return hashlib.sha256(
        encoded
    ).hexdigest()


def _network_observation(
    *,
    state_status: str = "finalized",
    reader=None,
):
    if reader is None:
        reader = FakePinnedReader()

    return build_network_index_observation(
        reader=reader,
        chain_id=1,
        contract_address=(
            "0x"
            + "77" * 20
        ),
        block_number=12345,
        state_status=state_status,
    )


def _transaction_observation(
    *,
    status_code: int = 7,
    status_name: str = "Finalized",
    execution_result: str = (
        "FINISHED_WITH_RETURN"
    ),
):
    return classify_transaction_observation(
        genlayer_tx_id=(
            "0x"
            + "ab" * 32
        ),
        status_code=status_code,
        status_name=status_name,
        execution_result=execution_result,
    )


class BackendPersistenceContractTests(
    unittest.TestCase
):
    @staticmethod
    def _api():
        return importlib.import_module(
            "backend.persistence"
        )

    def test_public_surface_is_versioned_and_explicit(
        self,
    ):
        api = self._api()

        self.assertEqual(
            api.PERSISTENCE_STATE_SCHEMA,
            "commit-backend-persistence-state-v1",
        )

        self.assertEqual(
            api.INDEX_RECORD_SCHEMA,
            "commit-persisted-index-observation-v1",
        )

        self.assertEqual(
            api.TRANSACTION_RECORD_SCHEMA,
            "commit-persisted-transaction-observation-v1",
        )

        self.assertEqual(
            api.INDEX_RECORD_KIND,
            "NETWORK_INDEX",
        )

        self.assertEqual(
            api.TRANSACTION_RECORD_KIND,
            "TRANSACTION",
        )

        self.assertTrue(
            issubclass(
                api.PersistenceError,
                ValueError,
            )
        )

        empty_signature = inspect.signature(
            api.empty_persistence_state
        )

        self.assertEqual(
            list(
                empty_signature.parameters
            ),
            [],
        )

        for name in (
            "apply_index_observation",
            "apply_transaction_observation",
        ):
            signature = inspect.signature(
                getattr(
                    api,
                    name,
                )
            )

            self.assertEqual(
                list(
                    signature.parameters
                ),
                [
                    "state",
                    "observation",
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

        validate_signature = (
            inspect.signature(
                api.validate_persistence_state
            )
        )

        self.assertEqual(
            list(
                validate_signature.parameters
            ),
            [
                "state",
            ],
        )

    def test_empty_state_shape_is_exact(
        self,
    ):
        api = self._api()

        state = (
            api.empty_persistence_state()
        )

        self.assertEqual(
            set(
                state
            ),
            {
                "schema",
                "index_records",
                "transaction_records",
            },
        )

        self.assertEqual(
            state[
                "schema"
            ],
            api.PERSISTENCE_STATE_SCHEMA,
        )

        self.assertEqual(
            state[
                "index_records"
            ],
            {},
        )

        self.assertEqual(
            state[
                "transaction_records"
            ],
            {},
        )

        api.validate_persistence_state(
            state
        )

    def test_index_record_identity_and_digest_are_deterministic(
        self,
    ):
        api = self._api()

        observation = (
            _network_observation()
        )

        state = (
            api.apply_index_observation(
                state=(
                    api.empty_persistence_state()
                ),
                observation=observation,
            )
        )

        expected_key = (
            "1:"
            + (
                "0x"
                + "77" * 20
            )
            + ":12345"
        )

        self.assertEqual(
            set(
                state[
                    "index_records"
                ]
            ),
            {
                expected_key,
            },
        )

        record = state[
            "index_records"
        ][
            expected_key
        ]

        self.assertEqual(
            set(
                record
            ),
            {
                "schema",
                "kind",
                "record_key",
                "payload_digest",
                "payload",
            },
        )

        self.assertEqual(
            record[
                "schema"
            ],
            api.INDEX_RECORD_SCHEMA,
        )

        self.assertEqual(
            record[
                "kind"
            ],
            api.INDEX_RECORD_KIND,
        )

        self.assertEqual(
            record[
                "record_key"
            ],
            expected_key,
        )

        self.assertEqual(
            record[
                "payload_digest"
            ],
            _canonical_digest(
                observation
            ),
        )

        self.assertEqual(
            record[
                "payload"
            ],
            observation,
        )

    def test_identical_index_replay_is_idempotent(
        self,
    ):
        api = self._api()

        observation = (
            _network_observation()
        )

        first = (
            api.apply_index_observation(
                state=(
                    api.empty_persistence_state()
                ),
                observation=observation,
            )
        )

        second = (
            api.apply_index_observation(
                state=first,
                observation=observation,
            )
        )

        self.assertEqual(
            second,
            first,
        )

    def test_provisional_index_can_promote_to_finalized(
        self,
    ):
        api = self._api()

        provisional = (
            _network_observation(
                state_status="accepted"
            )
        )

        finalized = (
            _network_observation(
                state_status="finalized"
            )
        )

        state = (
            api.apply_index_observation(
                state=(
                    api.empty_persistence_state()
                ),
                observation=provisional,
            )
        )

        promoted = (
            api.apply_index_observation(
                state=state,
                observation=finalized,
            )
        )

        self.assertEqual(
            len(
                promoted[
                    "index_records"
                ]
            ),
            1,
        )

        record = next(
            iter(
                promoted[
                    "index_records"
                ].values()
            )
        )

        self.assertEqual(
            record[
                "payload"
            ][
                "state_basis"
            ],
            "FINALIZED",
        )

        self.assertEqual(
            record[
                "payload_digest"
            ],
            _canonical_digest(
                finalized
            ),
        )

    def test_finalized_index_cannot_downgrade_to_provisional(
        self,
    ):
        api = self._api()

        state = (
            api.apply_index_observation(
                state=(
                    api.empty_persistence_state()
                ),
                observation=(
                    _network_observation(
                        state_status="finalized"
                    )
                ),
            )
        )

        with self.assertRaises(
            api.PersistenceError
        ):
            api.apply_index_observation(
                state=state,
                observation=(
                    _network_observation(
                        state_status="accepted"
                    )
                ),
            )

    def test_conflicting_finalized_index_is_rejected(
        self,
    ):
        api = self._api()

        first = (
            _network_observation(
                state_status="finalized"
            )
        )

        alternate_reader = (
            FakePinnedReader()
        )

        alternate_reader.source.protocol[
            "revision"
        ] = "alternate-reviewable-revision"

        conflicting = (
            _network_observation(
                state_status="finalized",
                reader=alternate_reader,
            )
        )

        self.assertNotEqual(
            _canonical_digest(
                first
            ),
            _canonical_digest(
                conflicting
            ),
        )

        state = (
            api.apply_index_observation(
                state=(
                    api.empty_persistence_state()
                ),
                observation=first,
            )
        )

        with self.assertRaises(
            api.PersistenceError
        ):
            api.apply_index_observation(
                state=state,
                observation=conflicting,
            )

    def test_transaction_record_identity_and_digest_are_deterministic(
        self,
    ):
        api = self._api()

        observation = (
            _transaction_observation()
        )

        state = (
            api.apply_transaction_observation(
                state=(
                    api.empty_persistence_state()
                ),
                observation=observation,
            )
        )

        expected_key = (
            "0x"
            + "ab" * 32
        )

        self.assertEqual(
            set(
                state[
                    "transaction_records"
                ]
            ),
            {
                expected_key,
            },
        )

        record = state[
            "transaction_records"
        ][
            expected_key
        ]

        self.assertEqual(
            set(
                record
            ),
            {
                "schema",
                "kind",
                "record_key",
                "payload_digest",
                "payload",
            },
        )

        self.assertEqual(
            record[
                "schema"
            ],
            api.TRANSACTION_RECORD_SCHEMA,
        )

        self.assertEqual(
            record[
                "kind"
            ],
            api.TRANSACTION_RECORD_KIND,
        )

        self.assertEqual(
            record[
                "record_key"
            ],
            expected_key,
        )

        self.assertEqual(
            record[
                "payload_digest"
            ],
            _canonical_digest(
                observation
            ),
        )

    def test_identical_transaction_replay_is_idempotent(
        self,
    ):
        api = self._api()

        observation = (
            _transaction_observation()
        )

        first = (
            api.apply_transaction_observation(
                state=(
                    api.empty_persistence_state()
                ),
                observation=observation,
            )
        )

        second = (
            api.apply_transaction_observation(
                state=first,
                observation=observation,
            )
        )

        self.assertEqual(
            second,
            first,
        )

    def test_accepted_transaction_can_promote_to_finalized(
        self,
    ):
        api = self._api()

        accepted = (
            _transaction_observation(
                status_code=5,
                status_name="Accepted",
            )
        )

        finalized = (
            _transaction_observation(
                status_code=7,
                status_name="Finalized",
            )
        )

        state = (
            api.apply_transaction_observation(
                state=(
                    api.empty_persistence_state()
                ),
                observation=accepted,
            )
        )

        promoted = (
            api.apply_transaction_observation(
                state=state,
                observation=finalized,
            )
        )

        self.assertEqual(
            len(
                promoted[
                    "transaction_records"
                ]
            ),
            1,
        )

        record = next(
            iter(
                promoted[
                    "transaction_records"
                ].values()
            )
        )

        self.assertIs(
            record[
                "payload"
            ][
                "finalized"
            ],
            True,
        )

        self.assertIs(
            record[
                "payload"
            ][
                "final_success"
            ],
            True,
        )

    def test_finalized_transaction_cannot_downgrade_to_accepted(
        self,
    ):
        api = self._api()

        state = (
            api.apply_transaction_observation(
                state=(
                    api.empty_persistence_state()
                ),
                observation=(
                    _transaction_observation(
                        status_code=7,
                        status_name="Finalized",
                    )
                ),
            )
        )

        with self.assertRaises(
            api.PersistenceError
        ):
            api.apply_transaction_observation(
                state=state,
                observation=(
                    _transaction_observation(
                        status_code=5,
                        status_name="Accepted",
                    )
                ),
            )

    def test_conflicting_finalized_transaction_is_rejected(
        self,
    ):
        api = self._api()

        successful = (
            _transaction_observation(
                status_code=7,
                status_name="Finalized",
                execution_result=(
                    "FINISHED_WITH_RETURN"
                ),
            )
        )

        failed = (
            _transaction_observation(
                status_code=7,
                status_name="Finalized",
                execution_result=(
                    "FINISHED_WITH_ERROR"
                ),
            )
        )

        state = (
            api.apply_transaction_observation(
                state=(
                    api.empty_persistence_state()
                ),
                observation=successful,
            )
        )

        with self.assertRaises(
            api.PersistenceError
        ):
            api.apply_transaction_observation(
                state=state,
                observation=failed,
            )

    def test_network_and_transaction_domains_remain_separate(
        self,
    ):
        api = self._api()

        state = (
            api.apply_index_observation(
                state=(
                    api.empty_persistence_state()
                ),
                observation=(
                    _network_observation()
                ),
            )
        )

        self.assertEqual(
            state[
                "transaction_records"
            ],
            {},
        )

        state = (
            api.apply_transaction_observation(
                state=state,
                observation=(
                    _transaction_observation()
                ),
            )
        )

        self.assertEqual(
            len(
                state[
                    "index_records"
                ]
            ),
            1,
        )

        self.assertEqual(
            len(
                state[
                    "transaction_records"
                ]
            ),
            1,
        )

        index_record = next(
            iter(
                state[
                    "index_records"
                ].values()
            )
        )

        transaction_record = next(
            iter(
                state[
                    "transaction_records"
                ].values()
            )
        )

        self.assertNotIn(
            "genlayer_tx_id",
            index_record[
                "payload"
            ],
        )

        self.assertNotIn(
            "index",
            transaction_record[
                "payload"
            ],
        )

    def test_forged_observations_are_rejected_before_persistence(
        self,
    ):
        api = self._api()

        forged_network = deepcopy(
            _network_observation(
                state_status="accepted"
            )
        )

        forged_network[
            "state_basis"
        ] = "FINALIZED"

        with self.assertRaises(
            (
                api.PersistenceError,
                NetworkAdapterError,
            )
        ):
            api.apply_index_observation(
                state=(
                    api.empty_persistence_state()
                ),
                observation=forged_network,
            )

        forged_transaction = deepcopy(
            _transaction_observation()
        )

        forged_transaction[
            "application_decision"
        ] = "COMMIT"

        with self.assertRaises(
            (
                api.PersistenceError,
                NetworkAdapterError,
            )
        ):
            api.apply_transaction_observation(
                state=(
                    api.empty_persistence_state()
                ),
                observation=forged_transaction,
            )

    def test_state_validator_rejects_unknown_fields(
        self,
    ):
        api = self._api()

        forged = {
            **api.empty_persistence_state(),
            "merged_application_state": {},
        }

        with self.assertRaises(
            api.PersistenceError
        ):
            api.validate_persistence_state(
                forged
            )

    def test_persisted_payloads_are_deeply_detached(
        self,
    ):
        api = self._api()

        observation = (
            _network_observation()
        )

        state = (
            api.apply_index_observation(
                state=(
                    api.empty_persistence_state()
                ),
                observation=observation,
            )
        )

        expected = deepcopy(
            state
        )

        observation[
            "index"
        ][
            "protocol"
        ][
            "revision"
        ] = "mutated-after-persist"

        self.assertEqual(
            state,
            expected,
        )

        api.validate_persistence_state(
            state
        )


if __name__ == "__main__":
    unittest.main()
