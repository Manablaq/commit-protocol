from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import math
import re
from typing import Any

from backend.network_adapter import (
    NetworkAdapterError,
    validate_network_index_observation,
    validate_transaction_observation,
)


PERSISTENCE_STATE_SCHEMA = (
    "commit-backend-persistence-state-v1"
)

INDEX_RECORD_SCHEMA = (
    "commit-persisted-index-observation-v1"
)

TRANSACTION_RECORD_SCHEMA = (
    "commit-persisted-transaction-observation-v1"
)

INDEX_RECORD_KIND = "NETWORK_INDEX"
TRANSACTION_RECORD_KIND = "TRANSACTION"


_STATE_FIELDS = {
    "schema",
    "index_records",
    "transaction_records",
}

_RECORD_FIELDS = {
    "schema",
    "kind",
    "record_key",
    "payload_digest",
    "payload",
}

_DIGEST_PATTERN = re.compile(
    r"^[0-9a-f]{64}$"
)


class PersistenceError(
    ValueError
):
    """Raised when a persistence projection is invalid."""


def _require_object(
    value: object,
    label: str,
) -> dict[str, Any]:
    if type(value) is not dict:
        raise PersistenceError(
            label
            + " must be an object"
        )

    return value


def _require_string(
    value: object,
    label: str,
) -> str:
    if (
        type(value) is not str
        or not value
    ):
        raise PersistenceError(
            label
            + " must be a nonempty string"
        )

    return value


def _validate_strict_json_value(
    value: object,
    *,
    value_path: str = "$",
) -> None:
    value_type = type(
        value
    )

    if (
        value is None
        or value_type is bool
        or value_type is int
        or value_type is str
    ):
        return

    if value_type is float:
        if not math.isfinite(
            value
        ):
            raise PersistenceError(
                value_path
                + " contains a non-finite JSON number"
            )

        return

    if value_type is list:
        for index, child in enumerate(
            value
        ):
            _validate_strict_json_value(
                child,
                value_path=(
                    value_path
                    + "["
                    + str(
                        index
                    )
                    + "]"
                ),
            )

        return

    if value_type is dict:
        for key, child in value.items():
            if type(
                key
            ) is not str:
                raise PersistenceError(
                    value_path
                    + " contains a non-string JSON object key"
                )

            _validate_strict_json_value(
                child,
                value_path=(
                    value_path
                    + "."
                    + key
                ),
            )

        return

    raise PersistenceError(
        value_path
        + " contains a non-JSON value of type "
        + value_type.__name__
    )


def _canonical_digest(
    value: object,
) -> str:
    _validate_strict_json_value(
        value
    )

    try:
        encoded = json.dumps(
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
    except (
        TypeError,
        ValueError,
    ) as exc:
        raise PersistenceError(
            "payload is not canonical-JSON serializable"
        ) from exc

    return hashlib.sha256(
        encoded
    ).hexdigest()


def _index_record_key(
    observation: dict[str, Any],
) -> str:
    chain_id = observation[
        "chain_id"
    ]

    contract_address = observation[
        "contract_address"
    ].lower()

    block_number = observation[
        "block_number"
    ]

    return (
        str(
            chain_id
        )
        + ":"
        + contract_address
        + ":"
        + str(
            block_number
        )
    )


def _transaction_record_key(
    observation: dict[str, Any],
) -> str:
    return observation[
        "genlayer_tx_id"
    ].lower()


def _make_record(
    *,
    schema: str,
    kind: str,
    record_key: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    detached_payload = deepcopy(
        payload
    )

    return {
        "schema": schema,
        "kind": kind,
        "record_key": record_key,
        "payload_digest": (
            _canonical_digest(
                detached_payload
            )
        ),
        "payload": detached_payload,
    }


def _validate_record_digest(
    record: dict[str, Any],
) -> None:
    digest = record.get(
        "payload_digest"
    )

    if (
        type(digest) is not str
        or _DIGEST_PATTERN.fullmatch(
            digest
        )
        is None
    ):
        raise PersistenceError(
            "payload_digest must be lowercase SHA-256 hex"
        )

    expected = _canonical_digest(
        record.get(
            "payload"
        )
    )

    if digest != expected:
        raise PersistenceError(
            "payload_digest does not match payload"
        )


def _validate_index_record(
    *,
    mapping_key: str,
    record_value: object,
) -> None:
    record = _require_object(
        record_value,
        "index record",
    )

    if set(record) != _RECORD_FIELDS:
        raise PersistenceError(
            "index record fields do not match schema"
        )

    if (
        record.get(
            "schema"
        )
        != INDEX_RECORD_SCHEMA
    ):
        raise PersistenceError(
            "invalid index record schema"
        )

    if (
        record.get(
            "kind"
        )
        != INDEX_RECORD_KIND
    ):
        raise PersistenceError(
            "invalid index record kind"
        )

    record_key = _require_string(
        record.get(
            "record_key"
        ),
        "index record_key",
    )

    if record_key != mapping_key:
        raise PersistenceError(
            "index record_key does not match mapping key"
        )

    payload = _require_object(
        record.get(
            "payload"
        ),
        "index record payload",
    )

    try:
        validate_network_index_observation(
            payload
        )
    except NetworkAdapterError as exc:
        raise PersistenceError(
            "invalid persisted network observation"
        ) from exc

    expected_key = _index_record_key(
        payload
    )

    if record_key != expected_key:
        raise PersistenceError(
            "index record identity does not match payload"
        )

    _validate_record_digest(
        record
    )


def _validate_transaction_record(
    *,
    mapping_key: str,
    record_value: object,
) -> None:
    record = _require_object(
        record_value,
        "transaction record",
    )

    if set(record) != _RECORD_FIELDS:
        raise PersistenceError(
            "transaction record fields do not match schema"
        )

    if (
        record.get(
            "schema"
        )
        != TRANSACTION_RECORD_SCHEMA
    ):
        raise PersistenceError(
            "invalid transaction record schema"
        )

    if (
        record.get(
            "kind"
        )
        != TRANSACTION_RECORD_KIND
    ):
        raise PersistenceError(
            "invalid transaction record kind"
        )

    record_key = _require_string(
        record.get(
            "record_key"
        ),
        "transaction record_key",
    )

    if record_key != mapping_key:
        raise PersistenceError(
            "transaction record_key does not match mapping key"
        )

    payload = _require_object(
        record.get(
            "payload"
        ),
        "transaction record payload",
    )

    try:
        validate_transaction_observation(
            payload
        )
    except NetworkAdapterError as exc:
        raise PersistenceError(
            "invalid persisted transaction observation"
        ) from exc

    expected_key = (
        _transaction_record_key(
            payload
        )
    )

    if record_key != expected_key:
        raise PersistenceError(
            "transaction record identity does not match payload"
        )

    _validate_record_digest(
        record
    )


def validate_persistence_state(
    state: object,
) -> dict[str, Any]:
    value = _require_object(
        state,
        "persistence state",
    )

    if set(value) != _STATE_FIELDS:
        raise PersistenceError(
            "persistence state fields do not match schema"
        )

    if (
        value.get(
            "schema"
        )
        != PERSISTENCE_STATE_SCHEMA
    ):
        raise PersistenceError(
            "invalid persistence state schema"
        )

    index_records = _require_object(
        value.get(
            "index_records"
        ),
        "index_records",
    )

    transaction_records = (
        _require_object(
            value.get(
                "transaction_records"
            ),
            "transaction_records",
        )
    )

    for mapping_key, record in (
        index_records.items()
    ):
        _require_string(
            mapping_key,
            "index mapping key",
        )

        _validate_index_record(
            mapping_key=mapping_key,
            record_value=record,
        )

    for mapping_key, record in (
        transaction_records.items()
    ):
        _require_string(
            mapping_key,
            "transaction mapping key",
        )

        _validate_transaction_record(
            mapping_key=mapping_key,
            record_value=record,
        )

    return value


def empty_persistence_state(
) -> dict[str, Any]:
    state = {
        "schema": (
            PERSISTENCE_STATE_SCHEMA
        ),
        "index_records": {},
        "transaction_records": {},
    }

    validate_persistence_state(
        state
    )

    return state


def apply_index_observation(
    *,
    state: object,
    observation: object,
) -> dict[str, Any]:
    validate_persistence_state(
        state
    )

    try:
        validated_observation = (
            validate_network_index_observation(
                observation
            )
        )
    except NetworkAdapterError as exc:
        raise PersistenceError(
            "network observation failed validation"
        ) from exc

    detached_observation = deepcopy(
        validated_observation
    )

    record_key = _index_record_key(
        detached_observation
    )

    incoming_record = _make_record(
        schema=INDEX_RECORD_SCHEMA,
        kind=INDEX_RECORD_KIND,
        record_key=record_key,
        payload=detached_observation,
    )

    next_state = deepcopy(
        state
    )

    existing = next_state[
        "index_records"
    ].get(
        record_key
    )

    if existing is None:
        next_state[
            "index_records"
        ][
            record_key
        ] = incoming_record

        validate_persistence_state(
            next_state
        )

        return next_state

    if (
        existing[
            "payload_digest"
        ]
        == incoming_record[
            "payload_digest"
        ]
    ):
        validate_persistence_state(
            next_state
        )

        return next_state

    existing_payload = existing[
        "payload"
    ]

    existing_finalized = (
        existing_payload[
            "state_basis"
        ]
        == "FINALIZED"
    )

    incoming_finalized = (
        detached_observation[
            "state_basis"
        ]
        == "FINALIZED"
    )

    if existing_finalized:
        if not incoming_finalized:
            raise PersistenceError(
                "finalized index observation cannot downgrade to provisional"
            )

        raise PersistenceError(
            "conflicting finalized index observation"
        )

    next_state[
        "index_records"
    ][
        record_key
    ] = incoming_record

    validate_persistence_state(
        next_state
    )

    return next_state


def apply_transaction_observation(
    *,
    state: object,
    observation: object,
) -> dict[str, Any]:
    validate_persistence_state(
        state
    )

    try:
        validated_observation = (
            validate_transaction_observation(
                observation
            )
        )
    except NetworkAdapterError as exc:
        raise PersistenceError(
            "transaction observation failed validation"
        ) from exc

    detached_observation = deepcopy(
        validated_observation
    )

    record_key = (
        _transaction_record_key(
            detached_observation
        )
    )

    incoming_record = _make_record(
        schema=(
            TRANSACTION_RECORD_SCHEMA
        ),
        kind=(
            TRANSACTION_RECORD_KIND
        ),
        record_key=record_key,
        payload=detached_observation,
    )

    next_state = deepcopy(
        state
    )

    existing = next_state[
        "transaction_records"
    ].get(
        record_key
    )

    if existing is None:
        next_state[
            "transaction_records"
        ][
            record_key
        ] = incoming_record

        validate_persistence_state(
            next_state
        )

        return next_state

    if (
        existing[
            "payload_digest"
        ]
        == incoming_record[
            "payload_digest"
        ]
    ):
        validate_persistence_state(
            next_state
        )

        return next_state

    existing_payload = existing[
        "payload"
    ]

    existing_finalized = (
        existing_payload[
            "finalized"
        ]
        is True
    )

    incoming_finalized = (
        detached_observation[
            "finalized"
        ]
        is True
    )

    if existing_finalized:
        if not incoming_finalized:
            raise PersistenceError(
                "finalized transaction observation cannot downgrade"
            )

        raise PersistenceError(
            "conflicting finalized transaction observation"
        )

    next_state[
        "transaction_records"
    ][
        record_key
    ] = incoming_record

    validate_persistence_state(
        next_state
    )

    return next_state
