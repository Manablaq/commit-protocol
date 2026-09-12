from __future__ import annotations

from backend.network_adapter import (
    build_network_index_observation,
    classify_transaction_observation,
)
from backend.persistence import (
    apply_index_observation,
    apply_transaction_observation,
)
from backend.storage_adapter import (
    StorageConflictError,
)


INGESTION_RUNNER_SCHEMA = (
    "commit-backend-ingestion-runner-v1"
)


class IngestionRunnerError(
    RuntimeError
):
    """Ingestion attempt failed safely."""


class IngestionConflictError(
    IngestionRunnerError
):
    """Durable-state compare-and-swap conflict."""


def _load_snapshot(
    *,
    store,
):
    try:
        snapshot = store.load()
    except Exception:
        raise IngestionRunnerError(
            "durable state read failed"
        ) from None

    if (
        type(snapshot) is not dict
        or "revision" not in snapshot
        or "state" not in snapshot
    ):
        raise IngestionRunnerError(
            "durable state snapshot is invalid"
        )

    revision = snapshot[
        "revision"
    ]

    state = snapshot[
        "state"
    ]

    if (
        type(revision) is not int
        or revision < 0
        or type(state) is not dict
    ):
        raise IngestionRunnerError(
            "durable state snapshot is invalid"
        )

    return (
        revision,
        state,
    )


def _save_transition(
    *,
    store,
    state,
    expected_revision,
):
    try:
        return store.save(
            state=state,
            expected_revision=(
                expected_revision
            ),
        )
    except StorageConflictError:
        raise IngestionConflictError(
            "durable state conflict"
        ) from None
    except Exception:
        raise IngestionRunnerError(
            "durable state write failed"
        ) from None


def ingest_index_observation(
    *,
    store,
    reader,
    chain_id,
    contract_address,
    block_number,
    state_status,
):
    revision, state = (
        _load_snapshot(
            store=store
        )
    )

    try:
        observation = (
            build_network_index_observation(
                reader=reader,
                chain_id=chain_id,
                contract_address=(
                    contract_address
                ),
                block_number=(
                    block_number
                ),
                state_status=(
                    state_status
                ),
            )
        )
    except Exception:
        raise IngestionRunnerError(
            "network observation failed"
        ) from None

    try:
        next_state = (
            apply_index_observation(
                state=state,
                observation=observation,
            )
        )
    except Exception:
        raise IngestionRunnerError(
            "ingestion transition failed"
        ) from None

    return _save_transition(
        store=store,
        state=next_state,
        expected_revision=revision,
    )


def ingest_transaction_observation(
    *,
    store,
    genlayer_tx_id,
    status_code,
    status_name,
    execution_result,
):
    revision, state = (
        _load_snapshot(
            store=store
        )
    )

    try:
        observation = (
            classify_transaction_observation(
                genlayer_tx_id=(
                    genlayer_tx_id
                ),
                status_code=status_code,
                status_name=status_name,
                execution_result=(
                    execution_result
                ),
            )
        )
    except Exception:
        raise IngestionRunnerError(
            "network observation failed"
        ) from None

    try:
        next_state = (
            apply_transaction_observation(
                state=state,
                observation=observation,
            )
        )
    except Exception:
        raise IngestionRunnerError(
            "ingestion transition failed"
        ) from None

    return _save_transition(
        store=store,
        state=next_state,
        expected_revision=revision,
    )
