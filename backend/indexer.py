from __future__ import annotations

from copy import deepcopy
from typing import Any


INDEX_SCHEMA = "commit-backend-index-v1"
SOURCE_MODE = "CANONICAL_PULL_READS"
FINALITY_STATUS = "UNVERIFIED"
EXECUTION_STATUS = "UNVERIFIED"


_SNAPSHOT_FIELDS = {
    "schema",
    "source_mode",
    "finality_status",
    "execution_status",
    "protocol",
    "missions",
    "withdrawals",
}

_MISSION_ENTRY_FIELDS = {
    "mission",
    "receipt",
    "manifest",
    "effects",
    "evidence",
}

_CROSS_CHECK_FIELDS = (
    "mission_id",
    "principal",
    "state",
    "objective",
    "policy_digest",
    "intent_digest",
    "effect_root",
    "evidence_root",
    "evaluation_evidence_root",
    "effect_count",
    "evidence_count",
    "decision",
    "reason_code",
    "prepare_deadline",
    "recovery_deadline",
    "allocation_applied",
)


class IndexerError(ValueError):
    """Raised when canonical read surfaces disagree or are malformed."""


def _require_object(
    value: object,
    label: str,
) -> dict[str, Any]:
    if type(value) is not dict:
        raise IndexerError(
            label
            + " must be an object"
        )

    return value


def _require_list(
    value: object,
    label: str,
) -> list[Any]:
    if type(value) is not list:
        raise IndexerError(
            label
            + " must be a list"
        )

    return value


def _require_count(
    value: object,
    label: str,
) -> int:
    if (
        type(value) is not int
        or value < 0
    ):
        raise IndexerError(
            label
            + " must be a nonnegative integer"
        )

    return value


def _require_identifier(
    value: object,
    label: str,
) -> str:
    if (
        type(value) is not str
        or not value
    ):
        raise IndexerError(
            label
            + " must be a nonempty string"
        )

    return value


def _source_read(
    source: object,
    method_name: str,
    *args: object,
) -> object:
    try:
        method = getattr(
            source,
            method_name,
        )

        return method(
            *args
        )
    except Exception as exc:
        raise IndexerError(
            "canonical source read failed: "
            + method_name
        ) from exc


def _validate_effect_records(
    *,
    mission_id: str,
    effects: list[Any],
) -> None:
    effect_ids: set[str] = set()

    for index, effect_value in enumerate(
        effects
    ):
        effect = _require_object(
            effect_value,
            "effect "
            + str(index),
        )

        if (
            effect.get(
                "mission_id"
            )
            != mission_id
        ):
            raise IndexerError(
                "effect mission_id does not match parent mission"
            )

        effect_id = _require_identifier(
            effect.get(
                "effect_id"
            ),
            "effect_id",
        )

        if effect_id in effect_ids:
            raise IndexerError(
                "duplicate effect_id"
            )

        effect_ids.add(
            effect_id
        )


def _validate_evidence_records(
    *,
    mission_id: str,
    evidence: list[Any],
) -> None:
    evidence_ids: set[str] = set()

    for index, evidence_value in enumerate(
        evidence
    ):
        item = _require_object(
            evidence_value,
            "evidence "
            + str(index),
        )

        if (
            item.get(
                "mission_id"
            )
            != mission_id
        ):
            raise IndexerError(
                "evidence mission_id does not match parent mission"
            )

        evidence_id = _require_identifier(
            item.get(
                "evidence_id"
            ),
            "evidence_id",
        )

        if evidence_id in evidence_ids:
            raise IndexerError(
                "duplicate evidence_id"
            )

        evidence_ids.add(
            evidence_id
        )


def _cross_check_mission_views(
    mission: dict[str, Any],
    receipt: dict[str, Any],
    manifest: dict[str, Any],
) -> None:
    for field in _CROSS_CHECK_FIELDS:
        if field not in mission:
            raise IndexerError(
                "mission missing cross-check field: "
                + field
            )

        if field not in receipt:
            raise IndexerError(
                "receipt missing cross-check field: "
                + field
            )

        if field not in manifest:
            raise IndexerError(
                "manifest missing cross-check field: "
                + field
            )

        mission_value = mission[
            field
        ]

        if (
            receipt[field]
            != mission_value
            or manifest[field]
            != mission_value
        ):
            raise IndexerError(
                "mission read surfaces disagree on: "
                + field
            )


def _manifest_evidence_projection(
    manifest_evidence: object,
) -> list[dict[str, Any]]:
    entries = _require_list(
        manifest_evidence,
        "manifest evidence",
    )

    projected: list[
        dict[str, Any]
    ] = []

    for index, value in enumerate(
        entries
    ):
        item = _require_object(
            value,
            "manifest evidence item "
            + str(index),
        )

        projected_item = {
            key: deepcopy(
                field_value
            )
            for key, field_value in item.items()
            if key != "authority"
        }

        projected.append(
            projected_item
        )

    return projected


def _validate_mission_entry(
    entry: object,
) -> dict[str, Any]:
    value = _require_object(
        entry,
        "mission entry",
    )

    if set(value) != _MISSION_ENTRY_FIELDS:
        raise IndexerError(
            "mission entry fields do not match index schema"
        )

    mission = _require_object(
        value.get(
            "mission"
        ),
        "mission",
    )

    receipt = _require_object(
        value.get(
            "receipt"
        ),
        "receipt",
    )

    manifest = _require_object(
        value.get(
            "manifest"
        ),
        "manifest",
    )

    effects = _require_list(
        value.get(
            "effects"
        ),
        "effects",
    )

    evidence = _require_list(
        value.get(
            "evidence"
        ),
        "evidence",
    )

    mission_id = _require_identifier(
        mission.get(
            "mission_id"
        ),
        "mission_id",
    )

    effect_count = _require_count(
        mission.get(
            "effect_count"
        ),
        "effect_count",
    )

    evidence_count = _require_count(
        mission.get(
            "evidence_count"
        ),
        "evidence_count",
    )

    if len(effects) != effect_count:
        raise IndexerError(
            "indexed effect count does not match mission"
        )

    if len(evidence) != evidence_count:
        raise IndexerError(
            "indexed evidence count does not match mission"
        )

    _validate_effect_records(
        mission_id=mission_id,
        effects=effects,
    )

    _validate_evidence_records(
        mission_id=mission_id,
        evidence=evidence,
    )

    _cross_check_mission_views(
        mission,
        receipt,
        manifest,
    )

    if (
        receipt.get(
            "mission_id"
        )
        != mission_id
        or manifest.get(
            "mission_id"
        )
        != mission_id
    ):
        raise IndexerError(
            "mission identifier mismatch"
        )

    manifest_effects = _require_list(
        manifest.get(
            "effects"
        ),
        "manifest effects",
    )

    if (
        manifest_effects
        != effects
    ):
        raise IndexerError(
            "manifest effects do not match indexed effects"
        )

    manifest_evidence = (
        _manifest_evidence_projection(
            manifest.get(
                "evidence"
            )
        )
    )

    if (
        manifest_evidence
        != evidence
    ):
        raise IndexerError(
            "manifest evidence does not match indexed evidence"
        )

    return value


def validate_index_snapshot(
    snapshot: object,
) -> dict[str, Any]:
    value = _require_object(
        snapshot,
        "snapshot",
    )

    if set(value) != _SNAPSHOT_FIELDS:
        raise IndexerError(
            "snapshot fields do not match index schema"
        )

    if (
        value.get(
            "schema"
        )
        != INDEX_SCHEMA
    ):
        raise IndexerError(
            "invalid index schema"
        )

    if (
        value.get(
            "source_mode"
        )
        != SOURCE_MODE
    ):
        raise IndexerError(
            "invalid index source mode"
        )

    if (
        value.get(
            "finality_status"
        )
        != FINALITY_STATUS
    ):
        raise IndexerError(
            "invalid finality status"
        )

    if (
        value.get(
            "execution_status"
        )
        != EXECUTION_STATUS
    ):
        raise IndexerError(
            "invalid execution status"
        )

    protocol = _require_object(
        value.get(
            "protocol"
        ),
        "protocol",
    )

    mission_count = _require_count(
        protocol.get(
            "mission_count"
        ),
        "protocol mission_count",
    )

    missions = _require_list(
        value.get(
            "missions"
        ),
        "missions",
    )

    if len(missions) != mission_count:
        raise IndexerError(
            "mission count does not match protocol"
        )

    mission_ids: set[
        str
    ] = set()

    for entry in missions:
        validated_entry = (
            _validate_mission_entry(
                entry
            )
        )

        mission_id = (
            validated_entry[
                "mission"
            ][
                "mission_id"
            ]
        )

        if mission_id in mission_ids:
            raise IndexerError(
                "duplicate mission_id"
            )

        mission_ids.add(
            mission_id
        )

    withdrawals = _require_list(
        value.get(
            "withdrawals"
        ),
        "withdrawals",
    )

    withdrawal_ids: set[
        str
    ] = set()

    for index, withdrawal_value in enumerate(
        withdrawals
    ):
        withdrawal = _require_object(
            withdrawal_value,
            "withdrawal",
        )

        withdrawal_id = (
            _require_identifier(
                withdrawal.get(
                    "withdrawal_id"
                ),
                "withdrawal_id",
            )
        )

        withdrawal_mission_id = _require_identifier(
            withdrawal.get(
                "mission_id"
            ),
            "withdrawal mission_id",
        )

        if (
            mission_ids
            and withdrawal_mission_id not in mission_ids
        ):
            raise IndexerError(
                "withdrawal references unknown mission"
            )

        expected_id = str(
            index
        )

        if withdrawal_id != expected_id:
            raise IndexerError(
                "withdrawal_id does not match canonical index"
            )

        if withdrawal_id in withdrawal_ids:
            raise IndexerError(
                "duplicate withdrawal_id"
            )

        withdrawal_ids.add(
            withdrawal_id
        )

    return value


def build_index_snapshot(
    *,
    source: object,
) -> dict[str, Any]:
    protocol = deepcopy(
        _source_read(
            source,
            "protocol_info",
        )
    )

    protocol = _require_object(
        protocol,
        "protocol",
    )

    mission_count = _require_count(
        protocol.get(
            "mission_count"
        ),
        "protocol mission_count",
    )

    missions: list[
        dict[str, Any]
    ] = []

    mission_ids: set[
        str
    ] = set()

    for mission_index in range(
        mission_count
    ):
        mission = deepcopy(
            _source_read(
                source,
                "get_mission_by_index",
                mission_index,
            )
        )

        mission = _require_object(
            mission,
            "mission",
        )

        mission_id = _require_identifier(
            mission.get(
                "mission_id"
            ),
            "mission_id",
        )

        if mission_id in mission_ids:
            raise IndexerError(
                "duplicate mission_id"
            )

        mission_ids.add(
            mission_id
        )

        effect_count = _require_count(
            mission.get(
                "effect_count"
            ),
            "effect_count",
        )

        evidence_count = _require_count(
            mission.get(
                "evidence_count"
            ),
            "evidence_count",
        )

        receipt = deepcopy(
            _source_read(
                source,
                "get_mission_receipt",
                mission_id,
            )
        )

        receipt = _require_object(
            receipt,
            "receipt",
        )

        manifest = deepcopy(
            _source_read(
                source,
                "get_mission_manifest",
                mission_id,
            )
        )

        manifest = _require_object(
            manifest,
            "manifest",
        )

        effects = [
            deepcopy(
                _source_read(
                    source,
                    "get_effect_by_index",
                    mission_id,
                    effect_index,
                )
            )
            for effect_index in range(
                effect_count
            )
        ]

        evidence = [
            deepcopy(
                _source_read(
                    source,
                    "get_evidence_by_index",
                    mission_id,
                    evidence_index,
                )
            )
            for evidence_index in range(
                evidence_count
            )
        ]

        entry = {
            "mission": mission,
            "receipt": receipt,
            "manifest": manifest,
            "effects": effects,
            "evidence": evidence,
        }

        _validate_mission_entry(
            entry
        )

        missions.append(
            entry
        )

    withdrawal_count_raw = _source_read(
        source,
        "get_withdrawal_count",
    )

    withdrawal_count = (
        _require_count(
            withdrawal_count_raw,
            "withdrawal_count",
        )
    )

    withdrawals: list[
        dict[str, Any]
    ] = []

    withdrawal_ids: set[
        str
    ] = set()

    for withdrawal_index in range(
        withdrawal_count
    ):
        withdrawal = deepcopy(
            _source_read(
                source,
                "get_withdrawal_by_index",
                withdrawal_index,
            )
        )

        withdrawal = _require_object(
            withdrawal,
            "withdrawal",
        )

        withdrawal_id = (
            _require_identifier(
                withdrawal.get(
                    "withdrawal_id"
                ),
                "withdrawal_id",
            )
        )

        expected_id = str(
            withdrawal_index
        )

        if withdrawal_id != expected_id:
            raise IndexerError(
                "withdrawal_id does not match canonical index"
            )

        if withdrawal_id in withdrawal_ids:
            raise IndexerError(
                "duplicate withdrawal_id"
            )

        withdrawal_ids.add(
            withdrawal_id
        )

        withdrawals.append(
            withdrawal
        )

    snapshot = {
        "schema": INDEX_SCHEMA,
        "source_mode": SOURCE_MODE,
        "finality_status": FINALITY_STATUS,
        "execution_status": EXECUTION_STATUS,
        "protocol": protocol,
        "missions": missions,
        "withdrawals": withdrawals,
    }

    validate_index_snapshot(
        snapshot
    )

    return snapshot
