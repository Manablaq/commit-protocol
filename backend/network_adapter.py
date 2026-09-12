from __future__ import annotations

import re
from typing import Any

from backend.indexer import (
    IndexerError,
    build_index_snapshot,
    validate_index_snapshot,
)


NETWORK_OBSERVATION_SCHEMA = (
    "commit-network-index-observation-v1"
)

TRANSACTION_OBSERVATION_SCHEMA = (
    "commit-network-transaction-observation-v1"
)

READ_MODE = "PINNED_CANONICAL_READS"

STATE_ACCEPTED = "accepted"
STATE_FINALIZED = "finalized"

TX_STATUS_ACCEPTED = 5
TX_STATUS_UNDETERMINED = 6
TX_STATUS_FINALIZED = 7
TX_STATUS_VALIDATORS_TIMEOUT = 11
TX_STATUS_LEADER_TIMEOUT = 12

EXECUTION_SUCCESS = "FINISHED_WITH_RETURN"


_NETWORK_OBSERVATION_FIELDS = {
    "schema",
    "read_mode",
    "chain_id",
    "contract_address",
    "block_number",
    "state_status",
    "state_basis",
    "network_identity_verified",
    "network_identity_basis",
    "index",
}

_TRANSACTION_OBSERVATION_FIELDS = {
    "schema",
    "genlayer_tx_id",
    "status_code",
    "status_name",
    "execution_result",
    "successful",
    "finalized",
    "final_success",
    "application_decision",
}

_STATUS_NAMES = {
    0: "Uninitialized",
    1: "Pending",
    2: "Proposing",
    3: "Committing",
    4: "Revealing",
    5: "Accepted",
    6: "Undetermined",
    7: "Finalized",
    8: "Canceled",
    9: "AppealRevealing",
    10: "AppealCommitting",
    11: "ValidatorsTimeout",
    12: "LeaderTimeout",
    13: "LeaderRevealing",
}

_SUCCESS_STATUS_CODES = {
    TX_STATUS_ACCEPTED,
    TX_STATUS_FINALIZED,
}

_TX_ID_PATTERN = re.compile(
    r"^0x[0-9a-fA-F]{64}$"
)

_ADDRESS_PATTERN = re.compile(
    r"^0x[0-9a-fA-F]{40}$"
)

_ZERO_ADDRESS = (
    "0x"
    + "00" * 20
)


class NetworkAdapterError(
    ValueError
):
    """Raised when a network observation is invalid."""


def _require_object(
    value: object,
    label: str,
) -> dict[str, Any]:
    if type(value) is not dict:
        raise NetworkAdapterError(
            label
            + " must be an object"
        )

    return value


def _require_list(
    value: object,
    label: str,
) -> list[Any]:
    if type(value) is not list:
        raise NetworkAdapterError(
            label
            + " must be a list"
        )

    return value


def _require_bool(
    value: object,
    label: str,
) -> bool:
    if type(value) is not bool:
        raise NetworkAdapterError(
            label
            + " must be a boolean"
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
        raise NetworkAdapterError(
            label
            + " must be a nonnegative integer"
        )

    return value


def _require_positive_uint(
    value: object,
    label: str,
) -> int:
    result = _require_uint(
        value,
        label,
    )

    if result == 0:
        raise NetworkAdapterError(
            label
            + " must be positive"
        )

    return result


def _require_address(
    value: object,
    label: str,
) -> str:
    if (
        type(value) is not str
        or _ADDRESS_PATTERN.fullmatch(
            value
        )
        is None
    ):
        raise NetworkAdapterError(
            label
            + " must be a 20-byte 0x-prefixed hex address"
        )

    if value.lower() == _ZERO_ADDRESS:
        raise NetworkAdapterError(
            label
            + " must not be the zero address"
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
        raise NetworkAdapterError(
            "genlayer_tx_id must be a 32-byte 0x-prefixed hex value"
        )

    return value


def _require_state_status(
    value: object,
) -> str:
    if value not in (
        STATE_ACCEPTED,
        STATE_FINALIZED,
    ):
        raise NetworkAdapterError(
            "state_status must be exactly accepted or finalized"
        )

    return value


def _require_execution_result(
    value: object,
) -> str:
    if (
        type(value) is not str
        or not value
    ):
        raise NetworkAdapterError(
            "execution_result must be a nonempty string"
        )

    return value


def _require_status_pair(
    *,
    status_code: object,
    status_name: object,
) -> tuple[int, str]:
    if type(status_code) is not int:
        raise NetworkAdapterError(
            "status_code must be an integer"
        )

    expected_name = _STATUS_NAMES.get(
        status_code
    )

    if expected_name is None:
        raise NetworkAdapterError(
            "unsupported transaction status code"
        )

    if (
        type(status_name) is not str
        or status_name != expected_name
    ):
        raise NetworkAdapterError(
            "transaction status code/name mismatch"
        )

    return (
        status_code,
        status_name,
    )


def _same_address(
    left: object,
    right: str,
) -> bool:
    return (
        type(left) is str
        and _ADDRESS_PATTERN.fullmatch(
            left
        )
        is not None
        and left.lower()
        == right.lower()
    )


class _PinnedCanonicalSource:
    def __init__(
        self,
        *,
        reader: object,
        block_number: int,
        state_status: str,
    ) -> None:
        self._reader = reader
        self._block_number = (
            block_number
        )
        self._state_status = (
            state_status
        )

    def _read(
        self,
        function_name: str,
        *args: object,
    ) -> object:
        try:
            read_contract = getattr(
                self._reader,
                "read_contract",
            )

            return read_contract(
                function_name=(
                    function_name
                ),
                args=tuple(
                    args
                ),
                block_number=(
                    self._block_number
                ),
                state_status=(
                    self._state_status
                ),
            )
        except Exception as exc:
            raise NetworkAdapterError(
                "pinned contract read failed: "
                + function_name
            ) from exc

    def protocol_info(
        self,
    ) -> object:
        return self._read(
            "protocol_info"
        )

    def get_mission_by_index(
        self,
        index: int,
    ) -> object:
        return self._read(
            "get_mission_by_index",
            index,
        )

    def get_mission_receipt(
        self,
        mission_id: str,
    ) -> object:
        return self._read(
            "get_mission_receipt",
            mission_id,
        )

    def get_mission_manifest(
        self,
        mission_id: str,
    ) -> object:
        return self._read(
            "get_mission_manifest",
            mission_id,
        )

    def get_effect_by_index(
        self,
        mission_id: str,
        index: int,
    ) -> object:
        return self._read(
            "get_effect_by_index",
            mission_id,
            index,
        )

    def get_evidence_by_index(
        self,
        mission_id: str,
        index: int,
    ) -> object:
        return self._read(
            "get_evidence_by_index",
            mission_id,
            index,
        )

    def get_withdrawal_count(
        self,
    ) -> object:
        return self._read(
            "get_withdrawal_count"
        )

    def get_withdrawal_by_index(
        self,
        index: int,
    ) -> object:
        return self._read(
            "get_withdrawal_by_index",
            index,
        )


def _validate_network_identity(
    *,
    index: dict[str, Any],
    chain_id: int,
    contract_address: str,
) -> None:
    missions = _require_list(
        index.get(
            "missions"
        ),
        "index missions",
    )

    for entry_value in missions:
        entry = _require_object(
            entry_value,
            "mission index entry",
        )

        for surface_name in (
            "receipt",
            "manifest",
        ):
            surface = _require_object(
                entry.get(
                    surface_name
                ),
                surface_name,
            )

            surface_chain_id = (
                surface.get(
                    "chain_id"
                )
            )

            if (
                type(surface_chain_id)
                is not int
                or surface_chain_id
                != chain_id
            ):
                raise NetworkAdapterError(
                    surface_name
                    + " chain_id does not match network observation"
                )

            coordinator = surface.get(
                "coordinator"
            )

            if not _same_address(
                coordinator,
                contract_address,
            ):
                raise NetworkAdapterError(
                    surface_name
                    + " coordinator does not match network observation"
                )

        receipt = entry[
            "receipt"
        ]

        manifest = entry[
            "manifest"
        ]

        if (
            receipt.get(
                "chain_id"
            )
            != manifest.get(
                "chain_id"
            )
        ):
            raise NetworkAdapterError(
                "receipt/manifest chain identity mismatch"
            )

        if not _same_address(
            receipt.get(
                "coordinator"
            ),
            contract_address,
        ):
            raise NetworkAdapterError(
                "receipt coordinator mismatch"
            )

        if not _same_address(
            manifest.get(
                "coordinator"
            ),
            contract_address,
        ):
            raise NetworkAdapterError(
                "manifest coordinator mismatch"
            )


def _network_identity_claim(
    *,
    index: dict[str, Any],
    chain_id: int,
    contract_address: str,
) -> tuple[bool, str]:
    missions = _require_list(
        index.get(
            "missions"
        ),
        "index missions",
    )

    if not missions:
        return (
            False,
            "UNVERIFIED_NO_MISSIONS",
        )

    _validate_network_identity(
        index=index,
        chain_id=chain_id,
        contract_address=(
            contract_address
        ),
    )

    return (
        True,
        "MISSION_RECEIPT_MANIFEST",
    )


def validate_network_index_observation(
    observation: object,
) -> dict[str, Any]:
    value = _require_object(
        observation,
        "network observation",
    )

    if set(value) != _NETWORK_OBSERVATION_FIELDS:
        raise NetworkAdapterError(
            "network observation fields do not match schema"
        )

    if (
        value.get(
            "schema"
        )
        != NETWORK_OBSERVATION_SCHEMA
    ):
        raise NetworkAdapterError(
            "invalid network observation schema"
        )

    if (
        value.get(
            "read_mode"
        )
        != READ_MODE
    ):
        raise NetworkAdapterError(
            "invalid network observation read mode"
        )

    chain_id = _require_positive_uint(
        value.get(
            "chain_id"
        ),
        "chain_id",
    )

    contract_address = (
        _require_address(
            value.get(
                "contract_address"
            ),
            "contract_address",
        )
    )

    _require_uint(
        value.get(
            "block_number"
        ),
        "block_number",
    )

    state_status = (
        _require_state_status(
            value.get(
                "state_status"
            )
        )
    )

    expected_state_basis = (
        "FINALIZED"
        if state_status
        == STATE_FINALIZED
        else "PROVISIONAL"
    )

    if (
        value.get(
            "state_basis"
        )
        != expected_state_basis
    ):
        raise NetworkAdapterError(
            "state_basis does not match state_status"
        )

    index = _require_object(
        value.get(
            "index"
        ),
        "index",
    )

    try:
        validate_index_snapshot(
            index
        )
    except IndexerError as exc:
        raise NetworkAdapterError(
            "invalid embedded index snapshot"
        ) from exc

    (
        expected_identity_verified,
        expected_identity_basis,
    ) = _network_identity_claim(
        index=index,
        chain_id=chain_id,
        contract_address=(
            contract_address
        ),
    )

    identity_verified = (
        _require_bool(
            value.get(
                "network_identity_verified"
            ),
            "network_identity_verified",
        )
    )

    if (
        identity_verified
        is not expected_identity_verified
    ):
        raise NetworkAdapterError(
            "network identity verification flag is inconsistent"
        )

    if (
        value.get(
            "network_identity_basis"
        )
        != expected_identity_basis
    ):
        raise NetworkAdapterError(
            "network identity basis is inconsistent"
        )

    return value


def _transaction_truth(
    *,
    status_code: int,
    execution_result: str,
) -> tuple[
    bool,
    bool,
    bool,
]:
    execution_succeeded = (
        execution_result
        == EXECUTION_SUCCESS
    )

    successful = (
        status_code
        in _SUCCESS_STATUS_CODES
        and execution_succeeded
    )

    finalized = (
        status_code
        == TX_STATUS_FINALIZED
    )

    final_success = (
        finalized
        and successful
    )

    return (
        successful,
        finalized,
        final_success,
    )


def validate_transaction_observation(
    observation: object,
) -> dict[str, Any]:
    value = _require_object(
        observation,
        "transaction observation",
    )

    if set(value) != _TRANSACTION_OBSERVATION_FIELDS:
        raise NetworkAdapterError(
            "transaction observation fields do not match schema"
        )

    if (
        value.get(
            "schema"
        )
        != TRANSACTION_OBSERVATION_SCHEMA
    ):
        raise NetworkAdapterError(
            "invalid transaction observation schema"
        )

    _require_tx_id(
        value.get(
            "genlayer_tx_id"
        )
    )

    (
        status_code,
        _status_name,
    ) = _require_status_pair(
        status_code=value.get(
            "status_code"
        ),
        status_name=value.get(
            "status_name"
        ),
    )

    execution_result = (
        _require_execution_result(
            value.get(
                "execution_result"
            )
        )
    )

    (
        expected_successful,
        expected_finalized,
        expected_final_success,
    ) = _transaction_truth(
        status_code=status_code,
        execution_result=(
            execution_result
        ),
    )

    successful = _require_bool(
        value.get(
            "successful"
        ),
        "successful",
    )

    finalized = _require_bool(
        value.get(
            "finalized"
        ),
        "finalized",
    )

    final_success = _require_bool(
        value.get(
            "final_success"
        ),
        "final_success",
    )

    if successful is not expected_successful:
        raise NetworkAdapterError(
            "successful field is inconsistent"
        )

    if finalized is not expected_finalized:
        raise NetworkAdapterError(
            "finalized field is inconsistent"
        )

    if (
        final_success
        is not expected_final_success
    ):
        raise NetworkAdapterError(
            "final_success field is inconsistent"
        )

    if (
        value.get(
            "application_decision"
        )
        is not None
    ):
        raise NetworkAdapterError(
            "protocol transaction status must not inject an application decision"
        )

    return value


def build_network_index_observation(
    *,
    reader: object,
    chain_id: int,
    contract_address: str,
    block_number: int,
    state_status: str,
) -> dict[str, Any]:
    checked_chain_id = (
        _require_positive_uint(
            chain_id,
            "chain_id",
        )
    )

    checked_contract_address = (
        _require_address(
            contract_address,
            "contract_address",
        )
    )

    checked_block_number = (
        _require_uint(
            block_number,
            "block_number",
        )
    )

    checked_state_status = (
        _require_state_status(
            state_status
        )
    )

    source = _PinnedCanonicalSource(
        reader=reader,
        block_number=(
            checked_block_number
        ),
        state_status=(
            checked_state_status
        ),
    )

    try:
        index = build_index_snapshot(
            source=source
        )
    except (
        IndexerError,
        NetworkAdapterError,
    ) as exc:
        raise NetworkAdapterError(
            "unable to build pinned network index observation"
        ) from exc

    (
        network_identity_verified,
        network_identity_basis,
    ) = _network_identity_claim(
        index=index,
        chain_id=checked_chain_id,
        contract_address=(
            checked_contract_address
        ),
    )

    state_basis = (
        "FINALIZED"
        if checked_state_status
        == STATE_FINALIZED
        else "PROVISIONAL"
    )

    observation = {
        "schema": (
            NETWORK_OBSERVATION_SCHEMA
        ),
        "read_mode": READ_MODE,
        "chain_id": (
            checked_chain_id
        ),
        "contract_address": (
            checked_contract_address
        ),
        "block_number": (
            checked_block_number
        ),
        "state_status": (
            checked_state_status
        ),
        "state_basis": (
            state_basis
        ),
        "network_identity_verified": (
            network_identity_verified
        ),
        "network_identity_basis": (
            network_identity_basis
        ),
        "index": index,
    }

    validate_network_index_observation(
        observation
    )

    return observation


def classify_transaction_observation(
    *,
    genlayer_tx_id: str,
    status_code: int,
    status_name: str,
    execution_result: str,
) -> dict[str, Any]:
    checked_tx_id = (
        _require_tx_id(
            genlayer_tx_id
        )
    )

    (
        checked_status_code,
        checked_status_name,
    ) = _require_status_pair(
        status_code=status_code,
        status_name=status_name,
    )

    checked_execution_result = (
        _require_execution_result(
            execution_result
        )
    )

    (
        successful,
        finalized,
        final_success,
    ) = _transaction_truth(
        status_code=(
            checked_status_code
        ),
        execution_result=(
            checked_execution_result
        ),
    )

    observation = {
        "schema": (
            TRANSACTION_OBSERVATION_SCHEMA
        ),
        "genlayer_tx_id": (
            checked_tx_id
        ),
        "status_code": (
            checked_status_code
        ),
        "status_name": (
            checked_status_name
        ),
        "execution_result": (
            checked_execution_result
        ),
        "successful": successful,
        "finalized": finalized,
        "final_success": (
            final_success
        ),
        "application_decision": None,
    }

    validate_transaction_observation(
        observation
    )

    return observation
