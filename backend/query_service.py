from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import math
import re
from typing import Any

from backend.indexer import (
    EXECUTION_STATUS,
    FINALITY_STATUS,
    INDEX_SCHEMA,
    SOURCE_MODE,
)
from backend.network_adapter import (
    NETWORK_OBSERVATION_SCHEMA,
    READ_MODE,
    TRANSACTION_OBSERVATION_SCHEMA,
    NetworkAdapterError,
    validate_network_index_observation,
    validate_transaction_observation,
)
from backend.persistence import (
    PersistenceError,
    validate_persistence_state,
)


INDEX_QUERY_SCHEMA = (
    "commit-backend-index-query-v1"
)

TRANSACTION_QUERY_SCHEMA = (
    "commit-backend-transaction-query-v1"
)

STATE_BASIS_FINALIZED = "FINALIZED"
STATE_BASIS_PROVISIONAL = "PROVISIONAL"


_ADDRESS_PATTERN = re.compile(
    r"^0x[0-9a-fA-F]{40}$"
)

_TX_ID_PATTERN = re.compile(
    r"^0x[0-9a-fA-F]{64}$"
)

_DIGEST_PATTERN = re.compile(
    r"^[0-9a-f]{64}$"
)

_ZERO_ADDRESS = (
    "0x"
    + "00" * 20
)

_INDEX_QUERY_FIELDS = {
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
}

_TRANSACTION_QUERY_FIELDS = {
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
}


class QueryServiceError(
    ValueError
):
    """Raised when a query request, state, or view is invalid."""


def _require_object(
    value: object,
    label: str,
) -> dict[str, Any]:
    if type(value) is not dict:
        raise QueryServiceError(
            label
            + " must be an object"
        )

    return value


def _require_list(
    value: object,
    label: str,
) -> list[Any]:
    if type(value) is not list:
        raise QueryServiceError(
            label
            + " must be a list"
        )

    return value


def _require_bool(
    value: object,
    label: str,
) -> bool:
    if type(value) is not bool:
        raise QueryServiceError(
            label
            + " must be a boolean"
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
        raise QueryServiceError(
            label
            + " must be a nonempty string"
        )

    return value


def _require_uint(
    value: object,
    label: str,
) -> int:
    if (
        type(value) is not int
        or value < 0
    ):
        raise QueryServiceError(
            label
            + " must be a nonnegative integer"
        )

    return value


def _validated_state(
    state: object,
) -> dict[str, Any]:
    try:
        return validate_persistence_state(
            state
        )
    except PersistenceError as exc:
        raise QueryServiceError(
            "invalid persistence state"
        ) from exc


def _require_chain_id(
    value: object,
) -> int:
    if (
        type(value) is not int
        or value <= 0
    ):
        raise QueryServiceError(
            "chain_id must be a positive integer"
        )

    return value


def _require_contract_address(
    value: object,
) -> str:
    if (
        type(value) is not str
        or _ADDRESS_PATTERN.fullmatch(
            value
        )
        is None
    ):
        raise QueryServiceError(
            "contract_address must be a 20-byte 0x-prefixed hex address"
        )

    if value.lower() == _ZERO_ADDRESS:
        raise QueryServiceError(
            "contract_address must not be the zero address"
        )

    return value


def _require_state_basis(
    value: object,
) -> str:
    if value not in (
        STATE_BASIS_FINALIZED,
        STATE_BASIS_PROVISIONAL,
    ):
        raise QueryServiceError(
            "state_basis must be exactly FINALIZED or PROVISIONAL"
        )

    return value


def _require_tx_id(
    value: object,
) -> str:
    if (
        type(value) is not str
        or _TX_ID_PATTERN.fullmatch(
            value
        )
        is None
    ):
        raise QueryServiceError(
            "genlayer_tx_id must be a 32-byte 0x-prefixed hex value"
        )

    return value


def _require_digest(
    value: object,
    label: str,
) -> str:
    if (
        type(value) is not str
        or _DIGEST_PATTERN.fullmatch(
            value
        )
        is None
    ):
        raise QueryServiceError(
            label
            + " must be lowercase SHA-256 hex"
        )

    return value


def _validate_strict_json_value(
    value: object,
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
            raise QueryServiceError(
                "query view contains a non-finite number"
            )

        return

    if value_type is list:
        for child in value:
            _validate_strict_json_value(
                child
            )

        return

    if value_type is dict:
        for key, child in value.items():
            if type(key) is not str:
                raise QueryServiceError(
                    "query view contains a non-string object key"
                )

            _validate_strict_json_value(
                child
            )

        return

    raise QueryServiceError(
        "query view contains a non-JSON value"
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
        UnicodeEncodeError,
    ) as exc:
        raise QueryServiceError(
            "query provenance payload is not canonical JSON"
        ) from exc

    return hashlib.sha256(
        encoded
    ).hexdigest()


def _expected_state_status(
    state_basis: str,
) -> str:
    if (
        state_basis
        == STATE_BASIS_FINALIZED
    ):
        return "finalized"

    return "accepted"


def _empty_index_view(
    *,
    chain_id: int,
    contract_address: str,
    requested_state_basis: str,
) -> dict[str, Any]:
    return {
        "schema": INDEX_QUERY_SCHEMA,
        "found": False,
        "chain_id": chain_id,
        "contract_address": (
            contract_address
        ),
        "requested_state_basis": (
            requested_state_basis
        ),
        "source_record_key": None,
        "source_payload_digest": None,
        "block_number": None,
        "state_status": None,
        "state_basis": None,
        "network_identity_verified": None,
        "network_identity_basis": None,
        "protocol": None,
        "missions": [],
        "withdrawals": [],
    }


def validate_index_query_view(
    view: object,
) -> dict[str, Any]:
    value = _require_object(
        view,
        "index query view",
    )

    if set(value) != _INDEX_QUERY_FIELDS:
        raise QueryServiceError(
            "index query view fields do not match schema"
        )

    if (
        value.get(
            "schema"
        )
        != INDEX_QUERY_SCHEMA
    ):
        raise QueryServiceError(
            "invalid index query schema"
        )

    found = _require_bool(
        value.get(
            "found"
        ),
        "found",
    )

    chain_id = _require_chain_id(
        value.get(
            "chain_id"
        )
    )

    contract_address = (
        _require_contract_address(
            value.get(
                "contract_address"
            )
        )
    )

    requested_state_basis = (
        _require_state_basis(
            value.get(
                "requested_state_basis"
            )
        )
    )

    if not found:
        nullable_fields = (
            "source_record_key",
            "source_payload_digest",
            "block_number",
            "state_status",
            "state_basis",
            "network_identity_verified",
            "network_identity_basis",
            "protocol",
        )

        for field in nullable_fields:
            if value.get(
                field
            ) is not None:
                raise QueryServiceError(
                    "not-found index query contains payload"
                )

        if value.get(
            "missions"
        ) != []:
            raise QueryServiceError(
                "not-found index query contains missions"
            )

        if value.get(
            "withdrawals"
        ) != []:
            raise QueryServiceError(
                "not-found index query contains withdrawals"
            )

        return value

    source_record_key = (
        _require_string(
            value.get(
                "source_record_key"
            ),
            "source_record_key",
        )
    )

    source_payload_digest = (
        _require_digest(
            value.get(
                "source_payload_digest"
            ),
            "source_payload_digest",
        )
    )

    block_number = _require_uint(
        value.get(
            "block_number"
        ),
        "block_number",
    )

    state_basis = (
        _require_state_basis(
            value.get(
                "state_basis"
            )
        )
    )

    if (
        state_basis
        != requested_state_basis
    ):
        raise QueryServiceError(
            "state_basis does not match requested_state_basis"
        )

    expected_status = (
        _expected_state_status(
            state_basis
        )
    )

    if (
        value.get(
            "state_status"
        )
        != expected_status
    ):
        raise QueryServiceError(
            "state_status does not match state_basis"
        )

    _require_bool(
        value.get(
            "network_identity_verified"
        ),
        "network_identity_verified",
    )

    _require_string(
        value.get(
            "network_identity_basis"
        ),
        "network_identity_basis",
    )

    protocol = _require_object(
        value.get(
            "protocol"
        ),
        "protocol",
    )

    missions = _require_list(
        value.get(
            "missions"
        ),
        "missions",
    )

    withdrawals = _require_list(
        value.get(
            "withdrawals"
        ),
        "withdrawals",
    )

    expected_record_key = (
        str(
            chain_id
        )
        + ":"
        + contract_address.lower()
        + ":"
        + str(
            block_number
        )
    )

    if (
        source_record_key
        != expected_record_key
    ):
        raise QueryServiceError(
            "source_record_key does not match query identity"
        )

    reconstructed_observation = {
        "schema": (
            NETWORK_OBSERVATION_SCHEMA
        ),
        "read_mode": READ_MODE,
        "chain_id": chain_id,
        "contract_address": (
            contract_address
        ),
        "block_number": (
            block_number
        ),
        "state_status": (
            value[
                "state_status"
            ]
        ),
        "state_basis": (
            state_basis
        ),
        "network_identity_verified": (
            value[
                "network_identity_verified"
            ]
        ),
        "network_identity_basis": (
            value[
                "network_identity_basis"
            ]
        ),
        "index": {
            "schema": INDEX_SCHEMA,
            "source_mode": (
                SOURCE_MODE
            ),
            "finality_status": (
                FINALITY_STATUS
            ),
            "execution_status": (
                EXECUTION_STATUS
            ),
            "protocol": protocol,
            "missions": missions,
            "withdrawals": withdrawals,
        },
    }

    try:
        validate_network_index_observation(
            reconstructed_observation
        )
    except NetworkAdapterError as exc:
        raise QueryServiceError(
            "index query view does not reconstruct a valid network observation"
        ) from exc

    expected_digest = (
        _canonical_digest(
            reconstructed_observation
        )
    )

    if (
        source_payload_digest
        != expected_digest
    ):
        raise QueryServiceError(
            "source_payload_digest does not match reconstructed observation"
        )

    return value


def build_index_query_view(
    *,
    state: object,
    chain_id: int,
    contract_address: str,
    state_basis: str,
) -> dict[str, Any]:
    validated_state = (
        _validated_state(
            state
        )
    )

    checked_chain_id = (
        _require_chain_id(
            chain_id
        )
    )

    requested_contract_address = (
        _require_contract_address(
            contract_address
        )
    )

    normalized_contract_address = (
        requested_contract_address.lower()
    )

    checked_state_basis = (
        _require_state_basis(
            state_basis
        )
    )

    selected: tuple[
        int,
        str,
        dict[str, Any],
    ] | None = None

    for (
        record_key,
        record_value,
    ) in validated_state[
        "index_records"
    ].items():
        record = record_value

        payload = record[
            "payload"
        ]

        if (
            payload[
                "chain_id"
            ]
            != checked_chain_id
        ):
            continue

        if (
            payload[
                "contract_address"
            ].lower()
            != normalized_contract_address
        ):
            continue

        if (
            payload[
                "state_basis"
            ]
            != checked_state_basis
        ):
            continue

        block_number = payload[
            "block_number"
        ]

        if (
            selected is None
            or block_number
            > selected[
                0
            ]
        ):
            selected = (
                block_number,
                record_key,
                record,
            )

    if selected is None:
        view = _empty_index_view(
            chain_id=checked_chain_id,
            contract_address=(
                normalized_contract_address
            ),
            requested_state_basis=(
                checked_state_basis
            ),
        )

        validate_index_query_view(
            view
        )

        return view

    (
        _block_number,
        record_key,
        record,
    ) = selected

    payload = record[
        "payload"
    ]

    index = payload[
        "index"
    ]

    view = {
        "schema": INDEX_QUERY_SCHEMA,
        "found": True,
        "chain_id": (
            checked_chain_id
        ),
        "contract_address": (
            payload[
                "contract_address"
            ]
        ),
        "requested_state_basis": (
            checked_state_basis
        ),
        "source_record_key": (
            record_key
        ),
        "source_payload_digest": (
            record[
                "payload_digest"
            ]
        ),
        "block_number": (
            payload[
                "block_number"
            ]
        ),
        "state_status": (
            payload[
                "state_status"
            ]
        ),
        "state_basis": (
            payload[
                "state_basis"
            ]
        ),
        "network_identity_verified": (
            payload[
                "network_identity_verified"
            ]
        ),
        "network_identity_basis": (
            payload[
                "network_identity_basis"
            ]
        ),
        "protocol": deepcopy(
            index[
                "protocol"
            ]
        ),
        "missions": deepcopy(
            index[
                "missions"
            ]
        ),
        "withdrawals": deepcopy(
            index[
                "withdrawals"
            ]
        ),
    }

    validate_index_query_view(
        view
    )

    return view


def _empty_transaction_view(
    *,
    genlayer_tx_id: str,
) -> dict[str, Any]:
    return {
        "schema": (
            TRANSACTION_QUERY_SCHEMA
        ),
        "found": False,
        "genlayer_tx_id": (
            genlayer_tx_id
        ),
        "source_record_key": None,
        "source_payload_digest": None,
        "status_code": None,
        "status_name": None,
        "execution_result": None,
        "successful": None,
        "finalized": None,
        "final_success": None,
        "application_decision": None,
    }


def validate_transaction_query_view(
    view: object,
) -> dict[str, Any]:
    value = _require_object(
        view,
        "transaction query view",
    )

    if (
        set(
            value
        )
        != _TRANSACTION_QUERY_FIELDS
    ):
        raise QueryServiceError(
            "transaction query view fields do not match schema"
        )

    if (
        value.get(
            "schema"
        )
        != TRANSACTION_QUERY_SCHEMA
    ):
        raise QueryServiceError(
            "invalid transaction query schema"
        )

    found = _require_bool(
        value.get(
            "found"
        ),
        "found",
    )

    genlayer_tx_id = (
        _require_tx_id(
            value.get(
                "genlayer_tx_id"
            )
        )
    )

    if not found:
        nullable_fields = (
            "source_record_key",
            "source_payload_digest",
            "status_code",
            "status_name",
            "execution_result",
            "successful",
            "finalized",
            "final_success",
            "application_decision",
        )

        for field in nullable_fields:
            if value.get(
                field
            ) is not None:
                raise QueryServiceError(
                    "not-found transaction query contains payload"
                )

        return value

    source_record_key = (
        _require_string(
            value.get(
                "source_record_key"
            ),
            "source_record_key",
        )
    )

    source_payload_digest = (
        _require_digest(
            value.get(
                "source_payload_digest"
            ),
            "source_payload_digest",
        )
    )

    if (
        source_record_key
        != genlayer_tx_id.lower()
    ):
        raise QueryServiceError(
            "source_record_key does not match genlayer_tx_id"
        )

    reconstructed_observation = {
        "schema": (
            TRANSACTION_OBSERVATION_SCHEMA
        ),
        "genlayer_tx_id": (
            genlayer_tx_id
        ),
        "status_code": (
            value.get(
                "status_code"
            )
        ),
        "status_name": (
            value.get(
                "status_name"
            )
        ),
        "execution_result": (
            value.get(
                "execution_result"
            )
        ),
        "successful": (
            value.get(
                "successful"
            )
        ),
        "finalized": (
            value.get(
                "finalized"
            )
        ),
        "final_success": (
            value.get(
                "final_success"
            )
        ),
        "application_decision": (
            value.get(
                "application_decision"
            )
        ),
    }

    try:
        validate_transaction_observation(
            reconstructed_observation
        )
    except NetworkAdapterError as exc:
        raise QueryServiceError(
            "transaction query view does not reconstruct a valid transaction observation"
        ) from exc

    expected_digest = (
        _canonical_digest(
            reconstructed_observation
        )
    )

    if (
        source_payload_digest
        != expected_digest
    ):
        raise QueryServiceError(
            "source_payload_digest does not match reconstructed transaction"
        )

    return value


def build_transaction_query_view(
    *,
    state: object,
    genlayer_tx_id: str,
) -> dict[str, Any]:
    validated_state = (
        _validated_state(
            state
        )
    )

    requested_tx_id = (
        _require_tx_id(
            genlayer_tx_id
        )
    )

    normalized_tx_id = (
        requested_tx_id.lower()
    )

    record = validated_state[
        "transaction_records"
    ].get(
        normalized_tx_id
    )

    if record is None:
        view = _empty_transaction_view(
            genlayer_tx_id=(
                normalized_tx_id
            )
        )

        validate_transaction_query_view(
            view
        )

        return view

    payload = record[
        "payload"
    ]

    view = {
        "schema": (
            TRANSACTION_QUERY_SCHEMA
        ),
        "found": True,
        "genlayer_tx_id": (
            payload[
                "genlayer_tx_id"
            ]
        ),
        "source_record_key": (
            record[
                "record_key"
            ]
        ),
        "source_payload_digest": (
            record[
                "payload_digest"
            ]
        ),
        "status_code": (
            payload[
                "status_code"
            ]
        ),
        "status_name": (
            payload[
                "status_name"
            ]
        ),
        "execution_result": (
            payload[
                "execution_result"
            ]
        ),
        "successful": (
            payload[
                "successful"
            ]
        ),
        "finalized": (
            payload[
                "finalized"
            ]
        ),
        "final_success": (
            payload[
                "final_success"
            ]
        ),
        "application_decision": (
            payload[
                "application_decision"
            ]
        ),
    }

    validate_transaction_query_view(
        view
    )

    return view
