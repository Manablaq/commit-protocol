from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib
import inspect
import json
import unittest

from backend.network_adapter import (
    classify_transaction_observation,
)
from backend.persistence import (
    apply_transaction_observation,
    empty_persistence_state,
)


TX_ID = (
    "0x"
    + "ab" * 32
)

NAMESPACE = (
    "commit-backend-state"
)


def _canonical_bytes(
    value,
) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(
            ",",
            ":",
        ),
        ensure_ascii=False,
        allow_nan=False,
    ).encode(
        "utf-8"
    )


def _digest(
    value,
) -> str:
    return hashlib.sha256(
        _canonical_bytes(
            value
        )
    ).hexdigest()


def _accepted_state():
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


def _finalized_state():
    state = _accepted_state()

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


class FakeAtomicDriver:
    def __init__(
        self,
    ):
        self.blobs = {}
        self.revisions = {}
        self.writes = 0
        self.reads = 0
        self.force_conflict = False
        self.read_error = None
        self.write_error = None

    def read(
        self,
        *,
        namespace: str,
    ):
        self.reads += 1

        if self.read_error is not None:
            raise self.read_error

        payload = self.blobs.get(
            namespace
        )

        if payload is None:
            return None

        return bytes(
            payload
        )

    def compare_and_swap(
        self,
        *,
        namespace: str,
        expected_revision: int,
        payload: bytes,
    ) -> bool:
        if self.write_error is not None:
            raise self.write_error

        if self.force_conflict:
            return False

        current_revision = (
            self.revisions.get(
                namespace,
                0,
            )
        )

        if (
            current_revision
            != expected_revision
        ):
            return False

        self.blobs[
            namespace
        ] = bytes(
            payload
        )

        self.revisions[
            namespace
        ] = (
            expected_revision
            + 1
        )

        self.writes += 1

        return True


class BackendStorageAdapterContractTests(
    unittest.TestCase
):
    @staticmethod
    def _api():
        return importlib.import_module(
            "backend.storage_adapter"
        )

    def _store(
        self,
        *,
        driver=None,
        namespace=NAMESPACE,
    ):
        api = self._api()

        if driver is None:
            driver = FakeAtomicDriver()

        return (
            api.DurableStateStore(
                driver=driver,
                namespace=namespace,
            ),
            driver,
        )

    def test_public_surface_is_versioned_and_explicit(
        self,
    ):
        api = self._api()

        self.assertEqual(
            api.STORAGE_SNAPSHOT_SCHEMA,
            "commit-backend-storage-snapshot-v1",
        )

        self.assertEqual(
            api.STORAGE_DRIVER_PROTOCOL,
            "ATOMIC_COMPARE_AND_SWAP_V1",
        )

        self.assertEqual(
            api.INITIAL_STORAGE_REVISION,
            0,
        )

        self.assertTrue(
            issubclass(
                api.StorageAdapterError,
                ValueError,
            )
        )

        self.assertTrue(
            issubclass(
                api.StorageConflictError,
                api.StorageAdapterError,
            )
        )

        self.assertTrue(
            issubclass(
                api.StorageCorruptionError,
                api.StorageAdapterError,
            )
        )

        signature = inspect.signature(
            api.DurableStateStore
        )

        self.assertEqual(
            list(
                signature.parameters
            ),
            [
                "driver",
                "namespace",
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

        save_signature = (
            inspect.signature(
                api.DurableStateStore.save
            )
        )

        self.assertEqual(
            list(
                save_signature.parameters
            ),
            [
                "self",
                "state",
                "expected_revision",
            ],
        )

        self.assertIs(
            save_signature.parameters[
                "state"
            ].kind,
            inspect.Parameter.KEYWORD_ONLY,
        )

        self.assertIs(
            save_signature.parameters[
                "expected_revision"
            ].kind,
            inspect.Parameter.KEYWORD_ONLY,
        )

    def test_missing_storage_loads_revision_zero_empty_state(
        self,
    ):
        api = self._api()

        store, driver = self._store()

        snapshot = store.load()

        self.assertEqual(
            set(
                snapshot
            ),
            {
                "schema",
                "revision",
                "state_digest",
                "state",
            },
        )

        expected_state = (
            empty_persistence_state()
        )

        self.assertEqual(
            snapshot[
                "schema"
            ],
            api.STORAGE_SNAPSHOT_SCHEMA,
        )

        self.assertEqual(
            snapshot[
                "revision"
            ],
            0,
        )

        self.assertEqual(
            snapshot[
                "state"
            ],
            expected_state,
        )

        self.assertEqual(
            snapshot[
                "state_digest"
            ],
            _digest(
                expected_state
            ),
        )

        self.assertEqual(
            driver.writes,
            0,
        )

    def test_first_save_commits_revision_one(
        self,
    ):
        store, driver = self._store()

        state = _accepted_state()

        snapshot = store.save(
            state=state,
            expected_revision=0,
        )

        self.assertEqual(
            snapshot[
                "revision"
            ],
            1,
        )

        self.assertEqual(
            snapshot[
                "state"
            ],
            state,
        )

        self.assertEqual(
            snapshot[
                "state_digest"
            ],
            _digest(
                state
            ),
        )

        self.assertEqual(
            driver.revisions[
                NAMESPACE
            ],
            1,
        )

        self.assertEqual(
            driver.writes,
            1,
        )

    def test_restart_reloads_saved_state(
        self,
    ):
        driver = FakeAtomicDriver()

        store_one, _ = self._store(
            driver=driver
        )

        state = _accepted_state()

        saved = store_one.save(
            state=state,
            expected_revision=0,
        )

        store_two, _ = self._store(
            driver=driver
        )

        loaded = store_two.load()

        self.assertEqual(
            loaded,
            saved,
        )

        self.assertEqual(
            loaded[
                "revision"
            ],
            1,
        )

    def test_identical_replay_is_idempotent_without_revision_bump(
        self,
    ):
        store, driver = self._store()

        state = _accepted_state()

        first = store.save(
            state=state,
            expected_revision=0,
        )

        second = store.save(
            state=deepcopy(
                state
            ),
            expected_revision=1,
        )

        self.assertEqual(
            second,
            first,
        )

        self.assertEqual(
            second[
                "revision"
            ],
            1,
        )

        self.assertEqual(
            driver.writes,
            1,
        )

    def test_stale_revision_conflict_does_not_overwrite(
        self,
    ):
        api = self._api()

        store, _driver = self._store()

        accepted = _accepted_state()
        finalized = _finalized_state()

        store.save(
            state=accepted,
            expected_revision=0,
        )

        with self.assertRaises(
            api.StorageConflictError
        ):
            store.save(
                state=finalized,
                expected_revision=0,
            )

        loaded = store.load()

        self.assertEqual(
            loaded[
                "revision"
            ],
            1,
        )

        self.assertEqual(
            loaded[
                "state"
            ],
            accepted,
        )

    def test_compare_and_swap_race_is_conflict(
        self,
    ):
        api = self._api()

        store, driver = self._store()

        driver.force_conflict = True

        with self.assertRaises(
            api.StorageConflictError
        ):
            store.save(
                state=_accepted_state(),
                expected_revision=0,
            )

        self.assertEqual(
            driver.writes,
            0,
        )

    def test_invalid_persistence_state_is_rejected_before_write(
        self,
    ):
        api = self._api()

        store, driver = self._store()

        forged = (
            empty_persistence_state()
        )

        forged[
            "unexpected"
        ] = True

        with self.assertRaises(
            api.StorageAdapterError
        ):
            store.save(
                state=forged,
                expected_revision=0,
            )

        self.assertEqual(
            driver.writes,
            0,
        )

    def test_corrupt_json_bytes_are_rejected(
        self,
    ):
        api = self._api()

        store, driver = self._store()

        driver.blobs[
            NAMESPACE
        ] = b"{not-json"

        driver.revisions[
            NAMESPACE
        ] = 1

        with self.assertRaises(
            api.StorageCorruptionError
        ):
            store.load()

    def test_state_digest_mismatch_is_rejected(
        self,
    ):
        api = self._api()

        store, driver = self._store()

        saved = store.save(
            state=_accepted_state(),
            expected_revision=0,
        )

        raw = json.loads(
            driver.blobs[
                NAMESPACE
            ].decode(
                "utf-8"
            )
        )

        raw[
            "state_digest"
        ] = (
            "0"
            * 64
        )

        driver.blobs[
            NAMESPACE
        ] = _canonical_bytes(
            raw
        )

        with self.assertRaises(
            api.StorageCorruptionError
        ):
            store.load()

        self.assertEqual(
            saved[
                "revision"
            ],
            1,
        )

    def test_snapshot_schema_and_unknown_fields_are_rejected(
        self,
    ):
        api = self._api()

        for mutation in (
            "schema",
            "unknown",
        ):
            with self.subTest(
                mutation=mutation
            ):
                store, driver = self._store()

                store.save(
                    state=_accepted_state(),
                    expected_revision=0,
                )

                raw = json.loads(
                    driver.blobs[
                        NAMESPACE
                    ].decode(
                        "utf-8"
                    )
                )

                if mutation == "schema":
                    raw[
                        "schema"
                    ] = "wrong-schema"
                else:
                    raw[
                        "extra"
                    ] = True

                driver.blobs[
                    NAMESPACE
                ] = _canonical_bytes(
                    raw
                )

                with self.assertRaises(
                    api.StorageCorruptionError
                ):
                    store.load()

    def test_driver_read_failure_is_normalized(
        self,
    ):
        api = self._api()

        store, driver = self._store()

        driver.read_error = RuntimeError(
            "driver read failure"
        )

        with self.assertRaises(
            api.StorageAdapterError
        ):
            store.load()

    def test_driver_write_failure_is_normalized(
        self,
    ):
        api = self._api()

        store, driver = self._store()

        driver.write_error = RuntimeError(
            "driver write failure"
        )

        with self.assertRaises(
            api.StorageAdapterError
        ):
            store.save(
                state=_accepted_state(),
                expected_revision=0,
            )

    def test_load_results_are_deeply_detached(
        self,
    ):
        store, _driver = self._store()

        state = _accepted_state()

        store.save(
            state=state,
            expected_revision=0,
        )

        loaded_one = store.load()
        loaded_two = store.load()

        loaded_one[
            "state"
        ][
            "transaction_records"
        ].clear()

        loaded_one[
            "revision"
        ] = 999

        self.assertNotEqual(
            loaded_one,
            loaded_two,
        )

        self.assertEqual(
            loaded_two[
                "state"
            ],
            state,
        )

        self.assertEqual(
            loaded_two[
                "revision"
            ],
            1,
        )

    def test_namespaces_are_isolated(
        self,
    ):
        driver = FakeAtomicDriver()

        store_a, _ = self._store(
            driver=driver,
            namespace="commit-a",
        )

        store_b, _ = self._store(
            driver=driver,
            namespace="commit-b",
        )

        state = _accepted_state()

        store_a.save(
            state=state,
            expected_revision=0,
        )

        loaded_a = store_a.load()
        loaded_b = store_b.load()

        self.assertEqual(
            loaded_a[
                "revision"
            ],
            1,
        )

        self.assertEqual(
            loaded_a[
                "state"
            ],
            state,
        )

        self.assertEqual(
            loaded_b[
                "revision"
            ],
            0,
        )

        self.assertEqual(
            loaded_b[
                "state"
            ],
            empty_persistence_state(),
        )


if __name__ == "__main__":
    unittest.main()
