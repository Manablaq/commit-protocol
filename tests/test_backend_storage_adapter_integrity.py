from __future__ import annotations

from copy import deepcopy
import importlib
import importlib.util
from pathlib import Path
import unittest

from backend.network_adapter import (
    classify_transaction_observation,
)
from backend.persistence import (
    apply_index_observation,
    apply_transaction_observation,
    empty_persistence_state,
)


TX_ID = (
    "0x"
    + "ab" * 32
)

TX_ID_TWO = (
    "0x"
    + "cd" * 32
)

NAMESPACE = (
    "commit-backend-state"
)


def _storage_fixture():
    file_name = Path(
        "tests/test_backend_storage_adapter_contract.py"
    )

    spec = importlib.util.spec_from_file_location(
        "commit_storage_integrity_fixture",
        file_name,
    )

    if (
        spec is None
        or spec.loader is None
    ):
        raise RuntimeError(
            "unable to load storage fixture"
        )

    module = importlib.util.module_from_spec(
        spec
    )

    spec.loader.exec_module(
        module
    )

    return module


def _query_fixture():
    file_name = Path(
        "tests/test_backend_query_service_contract.py"
    )

    spec = importlib.util.spec_from_file_location(
        "commit_storage_integrity_query_fixture",
        file_name,
    )

    if (
        spec is None
        or spec.loader is None
    ):
        raise RuntimeError(
            "unable to load query fixture"
        )

    module = importlib.util.module_from_spec(
        spec
    )

    spec.loader.exec_module(
        module
    )

    return module


STORAGE_FIXTURE = _storage_fixture()
QUERY_FIXTURE = _query_fixture()

FakeAtomicDriver = (
    STORAGE_FIXTURE.FakeAtomicDriver
)


def _accepted_transaction_state():
    observation = (
        classify_transaction_observation(
            genlayer_tx_id=TX_ID,
            status_code=5,
            status_name="Accepted",
            execution_result=(
                "FINISHED_WITH_RETURN"
            ),
        )
    )

    return (
        apply_transaction_observation(
            state=(
                empty_persistence_state()
            ),
            observation=observation,
        )
    )


def _finalized_transaction_state():
    state = (
        _accepted_transaction_state()
    )

    observation = (
        classify_transaction_observation(
            genlayer_tx_id=TX_ID,
            status_code=7,
            status_name="Finalized",
            execution_result=(
                "FINISHED_WITH_RETURN"
            ),
        )
    )

    return (
        apply_transaction_observation(
            state=state,
            observation=observation,
        )
    )


def _conflicting_finalized_transaction_state():
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

    return (
        apply_transaction_observation(
            state=(
                empty_persistence_state()
            ),
            observation=observation,
        )
    )


def _transaction_append_state():
    state = (
        _accepted_transaction_state()
    )

    observation = (
        classify_transaction_observation(
            genlayer_tx_id=TX_ID_TWO,
            status_code=5,
            status_name="Accepted",
            execution_result=(
                "FINISHED_WITH_RETURN"
            ),
        )
    )

    return (
        apply_transaction_observation(
            state=state,
            observation=observation,
        )
    )


def _index_state(
    *,
    state_status: str,
):
    observation = (
        QUERY_FIXTURE._index_observation(
            block_number=777,
            state_status=state_status,
        )
    )

    return (
        apply_index_observation(
            state=(
                empty_persistence_state()
            ),
            observation=observation,
        )
    )


class BackendStorageAdapterIntegrityTests(
    unittest.TestCase
):
    @staticmethod
    def _api():
        return importlib.import_module(
            "backend.storage_adapter"
        )

    def _store(
        self,
    ):
        api = self._api()

        driver = FakeAtomicDriver()

        store = api.DurableStateStore(
            driver=driver,
            namespace=NAMESPACE,
        )

        return (
            store,
            driver,
        )

    def test_transaction_finalized_to_accepted_rollback_is_rejected(
        self,
    ):
        api = self._api()

        store, _driver = self._store()

        store.save(
            state=(
                _finalized_transaction_state()
            ),
            expected_revision=0,
        )

        with self.assertRaises(
            api.StorageAdapterError
        ):
            store.save(
                state=(
                    _accepted_transaction_state()
                ),
                expected_revision=1,
            )

    def test_conflicting_finalized_transaction_replacement_is_rejected(
        self,
    ):
        api = self._api()

        store, _driver = self._store()

        store.save(
            state=(
                _finalized_transaction_state()
            ),
            expected_revision=0,
        )

        with self.assertRaises(
            api.StorageAdapterError
        ):
            store.save(
                state=(
                    _conflicting_finalized_transaction_state()
                ),
                expected_revision=1,
            )

    def test_transaction_record_deletion_is_rejected(
        self,
    ):
        api = self._api()

        store, _driver = self._store()

        finalized = (
            _finalized_transaction_state()
        )

        store.save(
            state=finalized,
            expected_revision=0,
        )

        deleted = deepcopy(
            finalized
        )

        deleted[
            "transaction_records"
        ].clear()

        with self.assertRaises(
            api.StorageAdapterError
        ):
            store.save(
                state=deleted,
                expected_revision=1,
            )

    def test_index_finalized_to_provisional_rollback_is_rejected(
        self,
    ):
        api = self._api()

        store, _driver = self._store()

        finalized = _index_state(
            state_status="finalized"
        )

        provisional = _index_state(
            state_status="accepted"
        )

        store.save(
            state=finalized,
            expected_revision=0,
        )

        with self.assertRaises(
            api.StorageAdapterError
        ):
            store.save(
                state=provisional,
                expected_revision=1,
            )

    def test_index_record_deletion_is_rejected(
        self,
    ):
        api = self._api()

        store, _driver = self._store()

        finalized = _index_state(
            state_status="finalized"
        )

        store.save(
            state=finalized,
            expected_revision=0,
        )

        deleted = deepcopy(
            finalized
        )

        deleted[
            "index_records"
        ].clear()

        with self.assertRaises(
            api.StorageAdapterError
        ):
            store.save(
                state=deleted,
                expected_revision=1,
            )

    def test_transaction_accepted_to_finalized_promotion_remains_allowed(
        self,
    ):
        store, _driver = self._store()

        first = store.save(
            state=(
                _accepted_transaction_state()
            ),
            expected_revision=0,
        )

        second = store.save(
            state=(
                _finalized_transaction_state()
            ),
            expected_revision=1,
        )

        self.assertEqual(
            first[
                "revision"
            ],
            1,
        )

        self.assertEqual(
            second[
                "revision"
            ],
            2,
        )

        self.assertEqual(
            second[
                "state"
            ],
            _finalized_transaction_state(),
        )

    def test_new_transaction_append_remains_allowed(
        self,
    ):
        store, _driver = self._store()

        first = store.save(
            state=(
                _accepted_transaction_state()
            ),
            expected_revision=0,
        )

        second = store.save(
            state=(
                _transaction_append_state()
            ),
            expected_revision=1,
        )

        self.assertEqual(
            first[
                "revision"
            ],
            1,
        )

        self.assertEqual(
            second[
                "revision"
            ],
            2,
        )

        self.assertEqual(
            len(
                second[
                    "state"
                ][
                    "transaction_records"
                ]
            ),
            2,
        )

    def test_index_provisional_to_finalized_promotion_remains_allowed(
        self,
    ):
        store, _driver = self._store()

        provisional = _index_state(
            state_status="accepted"
        )

        finalized = _index_state(
            state_status="finalized"
        )

        first = store.save(
            state=provisional,
            expected_revision=0,
        )

        second = store.save(
            state=finalized,
            expected_revision=1,
        )

        self.assertEqual(
            first[
                "revision"
            ],
            1,
        )

        self.assertEqual(
            second[
                "revision"
            ],
            2,
        )

        record = next(
            iter(
                second[
                    "state"
                ][
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


if __name__ == "__main__":
    unittest.main()
