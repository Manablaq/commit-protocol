from __future__ import annotations

import importlib
import inspect
from pathlib import Path
from unittest.mock import patch
import unittest

from backend.storage_adapter import (
    StorageConflictError,
)


CHAIN_ID = 1

CONTRACT_ADDRESS = (
    "0x"
    + "77" * 20
)

BLOCK_NUMBER = 12345

STATE_STATUS = "finalized"

TX_ID = (
    "0x"
    + "ab" * 32
)

STATUS_CODE = 7

STATUS_NAME = "Finalized"

EXECUTION_RESULT = (
    "FINISHED_WITH_RETURN"
)

REVISION = 7

_UNSET = object()


class FakeStore:
    def __init__(
        self,
        *,
        snapshot=_UNSET,
        load_error=None,
        save_error=None,
        saved_snapshot=None,
    ):
        self.snapshot = (
            {
                "revision": REVISION,
                "state": {
                    "fixture": "state",
                },
            }
            if snapshot is _UNSET
            else snapshot
        )

        self.load_error = (
            load_error
        )

        self.save_error = (
            save_error
        )

        self.saved_snapshot = (
            {
                "revision": (
                    REVISION
                    + 1
                ),
                "state": {
                    "fixture": (
                        "saved"
                    ),
                },
            }
            if saved_snapshot is None
            else saved_snapshot
        )

        self.loads = 0
        self.saves = []

    def load(
        self,
    ):
        self.loads += 1

        if (
            self.load_error
            is not None
        ):
            raise self.load_error

        return self.snapshot

    def save(
        self,
        *,
        state,
        expected_revision,
    ):
        self.saves.append(
            {
                "state": state,
                "expected_revision": (
                    expected_revision
                ),
            }
        )

        if (
            self.save_error
            is not None
        ):
            raise self.save_error

        return self.saved_snapshot


class IngestionRunnerContractTests(
    unittest.TestCase
):
    @staticmethod
    def _api():
        return importlib.import_module(
            "backend.ingestion_runner"
        )

    def test_public_surface_and_signatures_are_exact(
        self,
    ):
        api = self._api()

        self.assertEqual(
            api.INGESTION_RUNNER_SCHEMA,
            "commit-backend-ingestion-runner-v1",
        )

        self.assertTrue(
            issubclass(
                api.IngestionRunnerError,
                RuntimeError,
            )
        )

        self.assertTrue(
            issubclass(
                api.IngestionConflictError,
                api.IngestionRunnerError,
            )
        )

        index_signature = inspect.signature(
            api.ingest_index_observation
        )

        self.assertEqual(
            list(
                index_signature.parameters
            ),
            [
                "store",
                "reader",
                "chain_id",
                "contract_address",
                "block_number",
                "state_status",
            ],
        )

        transaction_signature = (
            inspect.signature(
                api.ingest_transaction_observation
            )
        )

        self.assertEqual(
            list(
                transaction_signature.parameters
            ),
            [
                "store",
                "genlayer_tx_id",
                "status_code",
                "status_name",
                "execution_result",
            ],
        )

        for signature in (
            index_signature,
            transaction_signature,
        ):
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

    def test_index_ingestion_order_and_expected_revision_are_exact(
        self,
    ):
        api = self._api()

        store = FakeStore()

        reader = object()

        observation = {
            "fixture": (
                "index-observation"
            ),
        }

        next_state = {
            "fixture": (
                "index-next-state"
            ),
        }

        events = []

        def build(
            **kwargs,
        ):
            events.append(
                (
                    "observe",
                    kwargs,
                )
            )

            return observation

        def apply(
            **kwargs,
        ):
            events.append(
                (
                    "apply",
                    kwargs,
                )
            )

            return next_state

        original_load = store.load
        original_save = store.save

        def load():
            events.append(
                (
                    "load",
                    {},
                )
            )

            return original_load()

        def save(
            *,
            state,
            expected_revision,
        ):
            events.append(
                (
                    "save",
                    {
                        "state": state,
                        "expected_revision": (
                            expected_revision
                        ),
                    },
                )
            )

            return original_save(
                state=state,
                expected_revision=(
                    expected_revision
                ),
            )

        store.load = load
        store.save = save

        with (
            patch.object(
                api,
                "build_network_index_observation",
                side_effect=build,
            ),
            patch.object(
                api,
                "apply_index_observation",
                side_effect=apply,
            ),
        ):
            result = (
                api.ingest_index_observation(
                    store=store,
                    reader=reader,
                    chain_id=CHAIN_ID,
                    contract_address=(
                        CONTRACT_ADDRESS
                    ),
                    block_number=(
                        BLOCK_NUMBER
                    ),
                    state_status=(
                        STATE_STATUS
                    ),
                )
            )

        self.assertIs(
            result,
            store.saved_snapshot,
        )

        self.assertEqual(
            store.loads,
            1,
        )

        self.assertEqual(
            store.saves,
            [
                {
                    "state": (
                        next_state
                    ),
                    "expected_revision": (
                        REVISION
                    ),
                },
            ],
        )

        self.assertEqual(
            events,
            [
                (
                    "load",
                    {},
                ),
                (
                    "observe",
                    {
                        "reader": reader,
                        "chain_id": (
                            CHAIN_ID
                        ),
                        "contract_address": (
                            CONTRACT_ADDRESS
                        ),
                        "block_number": (
                            BLOCK_NUMBER
                        ),
                        "state_status": (
                            STATE_STATUS
                        ),
                    },
                ),
                (
                    "apply",
                    {
                        "state": (
                            store.snapshot[
                                "state"
                            ]
                        ),
                        "observation": (
                            observation
                        ),
                    },
                ),
                (
                    "save",
                    {
                        "state": (
                            next_state
                        ),
                        "expected_revision": (
                            REVISION
                        ),
                    },
                ),
            ],
        )

    def test_transaction_ingestion_order_and_expected_revision_are_exact(
        self,
    ):
        api = self._api()

        store = FakeStore()

        observation = {
            "fixture": (
                "transaction-observation"
            ),
        }

        next_state = {
            "fixture": (
                "transaction-next-state"
            ),
        }

        events = []

        def build(
            **kwargs,
        ):
            events.append(
                (
                    "observe",
                    kwargs,
                )
            )

            return observation

        def apply(
            **kwargs,
        ):
            events.append(
                (
                    "apply",
                    kwargs,
                )
            )

            return next_state

        original_load = store.load
        original_save = store.save

        def load():
            events.append(
                (
                    "load",
                    {},
                )
            )

            return original_load()

        def save(
            *,
            state,
            expected_revision,
        ):
            events.append(
                (
                    "save",
                    {
                        "state": state,
                        "expected_revision": (
                            expected_revision
                        ),
                    },
                )
            )

            return original_save(
                state=state,
                expected_revision=(
                    expected_revision
                ),
            )

        store.load = load
        store.save = save

        with (
            patch.object(
                api,
                "classify_transaction_observation",
                side_effect=build,
            ),
            patch.object(
                api,
                "apply_transaction_observation",
                side_effect=apply,
            ),
        ):
            result = (
                api.ingest_transaction_observation(
                    store=store,
                    genlayer_tx_id=TX_ID,
                    status_code=(
                        STATUS_CODE
                    ),
                    status_name=(
                        STATUS_NAME
                    ),
                    execution_result=(
                        EXECUTION_RESULT
                    ),
                )
            )

        self.assertIs(
            result,
            store.saved_snapshot,
        )

        self.assertEqual(
            store.loads,
            1,
        )

        self.assertEqual(
            store.saves,
            [
                {
                    "state": (
                        next_state
                    ),
                    "expected_revision": (
                        REVISION
                    ),
                },
            ],
        )

        self.assertEqual(
            events,
            [
                (
                    "load",
                    {},
                ),
                (
                    "observe",
                    {
                        "genlayer_tx_id": (
                            TX_ID
                        ),
                        "status_code": (
                            STATUS_CODE
                        ),
                        "status_name": (
                            STATUS_NAME
                        ),
                        "execution_result": (
                            EXECUTION_RESULT
                        ),
                    },
                ),
                (
                    "apply",
                    {
                        "state": (
                            store.snapshot[
                                "state"
                            ]
                        ),
                        "observation": (
                            observation
                        ),
                    },
                ),
                (
                    "save",
                    {
                        "state": (
                            next_state
                        ),
                        "expected_revision": (
                            REVISION
                        ),
                    },
                ),
            ],
        )

    def test_malformed_loaded_snapshot_fails_before_observation_or_write(
        self,
    ):
        api = self._api()

        malformed = (
            None,
            {},
            {
                "revision": REVISION,
            },
            {
                "state": {},
            },
            {
                "revision": True,
                "state": {},
            },
            {
                "revision": -1,
                "state": {},
            },
        )

        for snapshot in malformed:
            with self.subTest(
                snapshot=repr(
                    snapshot
                )
            ):
                store = FakeStore(
                    snapshot=snapshot
                )

                with (
                    patch.object(
                        api,
                        "build_network_index_observation",
                    ) as build,
                    patch.object(
                        api,
                        "apply_index_observation",
                    ) as apply,
                ):
                    with self.assertRaises(
                        api.IngestionRunnerError
                    ):
                        api.ingest_index_observation(
                            store=store,
                            reader=object(),
                            chain_id=CHAIN_ID,
                            contract_address=(
                                CONTRACT_ADDRESS
                            ),
                            block_number=(
                                BLOCK_NUMBER
                            ),
                            state_status=(
                                STATE_STATUS
                            ),
                        )

                build.assert_not_called()
                apply.assert_not_called()

                self.assertEqual(
                    store.saves,
                    [],
                )

    def test_network_observation_failure_is_sanitized_and_never_written(
        self,
    ):
        api = self._api()

        store = FakeStore()

        with (
            patch.object(
                api,
                "build_network_index_observation",
                side_effect=ValueError(
                    "secret network observation detail"
                ),
            ),
            patch.object(
                api,
                "apply_index_observation",
            ) as apply,
        ):
            try:
                api.ingest_index_observation(
                    store=store,
                    reader=object(),
                    chain_id=CHAIN_ID,
                    contract_address=(
                        CONTRACT_ADDRESS
                    ),
                    block_number=(
                        BLOCK_NUMBER
                    ),
                    state_status=(
                        STATE_STATUS
                    ),
                )
            except api.IngestionRunnerError as exc:
                rendered = str(
                    exc
                ).lower()
            else:
                self.fail(
                    "network observation failure was accepted"
                )

        apply.assert_not_called()

        self.assertEqual(
            store.saves,
            [],
        )

        self.assertNotIn(
            "secret",
            rendered,
        )

        self.assertNotIn(
            "network observation detail",
            rendered,
        )

    def test_invalid_transition_failure_is_sanitized_and_never_written(
        self,
    ):
        api = self._api()

        store = FakeStore()

        observation = {
            "fixture": (
                "observation"
            ),
        }

        with (
            patch.object(
                api,
                "build_network_index_observation",
                return_value=observation,
            ),
            patch.object(
                api,
                "apply_index_observation",
                side_effect=ValueError(
                    "secret transition detail"
                ),
            ),
        ):
            try:
                api.ingest_index_observation(
                    store=store,
                    reader=object(),
                    chain_id=CHAIN_ID,
                    contract_address=(
                        CONTRACT_ADDRESS
                    ),
                    block_number=(
                        BLOCK_NUMBER
                    ),
                    state_status=(
                        STATE_STATUS
                    ),
                )
            except api.IngestionRunnerError as exc:
                rendered = str(
                    exc
                ).lower()
            else:
                self.fail(
                    "invalid transition was accepted"
                )

        self.assertEqual(
            store.saves,
            [],
        )

        self.assertNotIn(
            "secret",
            rendered,
        )

        self.assertNotIn(
            "transition detail",
            rendered,
        )

    def test_storage_conflict_is_explicit_and_has_no_hidden_retry(
        self,
    ):
        api = self._api()

        store = FakeStore(
            save_error=StorageConflictError(
                "secret CAS conflict detail"
            )
        )

        observation = {
            "fixture": (
                "observation"
            ),
        }

        next_state = {
            "fixture": (
                "next-state"
            ),
        }

        with (
            patch.object(
                api,
                "build_network_index_observation",
                return_value=observation,
            ),
            patch.object(
                api,
                "apply_index_observation",
                return_value=next_state,
            ),
        ):
            try:
                api.ingest_index_observation(
                    store=store,
                    reader=object(),
                    chain_id=CHAIN_ID,
                    contract_address=(
                        CONTRACT_ADDRESS
                    ),
                    block_number=(
                        BLOCK_NUMBER
                    ),
                    state_status=(
                        STATE_STATUS
                    ),
                )
            except api.IngestionConflictError as exc:
                rendered = str(
                    exc
                ).lower()
            else:
                self.fail(
                    "storage conflict was silently accepted"
                )

        self.assertEqual(
            store.loads,
            1,
        )

        self.assertEqual(
            len(
                store.saves
            ),
            1,
        )

        self.assertEqual(
            store.saves[
                0
            ][
                "expected_revision"
            ],
            REVISION,
        )

        self.assertNotIn(
            "secret",
            rendered,
        )

        self.assertNotIn(
            "cas conflict detail",
            rendered,
        )

    def test_nonconflict_storage_failure_is_sanitized_without_retry(
        self,
    ):
        api = self._api()

        store = FakeStore(
            save_error=RuntimeError(
                "secret durable write detail"
            )
        )

        with (
            patch.object(
                api,
                "build_network_index_observation",
                return_value={
                    "fixture": (
                        "observation"
                    ),
                },
            ),
            patch.object(
                api,
                "apply_index_observation",
                return_value={
                    "fixture": (
                        "next-state"
                    ),
                },
            ),
        ):
            try:
                api.ingest_index_observation(
                    store=store,
                    reader=object(),
                    chain_id=CHAIN_ID,
                    contract_address=(
                        CONTRACT_ADDRESS
                    ),
                    block_number=(
                        BLOCK_NUMBER
                    ),
                    state_status=(
                        STATE_STATUS
                    ),
                )
            except api.IngestionRunnerError as exc:
                rendered = str(
                    exc
                ).lower()
            else:
                self.fail(
                    "durable write failure was silently accepted"
                )

        self.assertEqual(
            store.loads,
            1,
        )

        self.assertEqual(
            len(
                store.saves
            ),
            1,
        )

        self.assertNotIn(
            "secret",
            rendered,
        )

        self.assertNotIn(
            "durable write detail",
            rendered,
        )

    def test_library_has_no_environment_database_schema_public_route_or_filesystem_coupling(
        self,
    ):
        self._api()

        source = Path(
            "backend/ingestion_runner.py"
        ).read_text()

        forbidden = (
            "os.environ",
            "os.getenv",
            "psycopg.connect(",
            "SCHEMA_SQL",
            "schema_bootstrap",
            "FastAPI",
            "backend.service_api",
            "backend.production_app",
            "api/index.py",
            "requests",
            "httpx",
            "open(",
            "Path(",
        )

        for term in forbidden:
            self.assertNotIn(
                term,
                source,
            )

        required = (
            "build_network_index_observation",
            "classify_transaction_observation",
            "apply_index_observation",
            "apply_transaction_observation",
            "StorageConflictError",
        )

        for term in required:
            self.assertIn(
                term,
                source,
            )

    def test_public_app_entrypoint_and_schema_bootstrap_do_not_import_ingestion_runner(
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
            Path(
                "backend/schema_bootstrap.py"
            ),
            Path(
                "scripts/bootstrap_backend_schema.py"
            ),
        )

        for file_name in targets:
            with self.subTest(
                file_name=str(
                    file_name
                )
            ):
                source = (
                    file_name.read_text()
                )

                self.assertNotIn(
                    "ingestion_runner",
                    source,
                )


if __name__ == "__main__":
    unittest.main()
