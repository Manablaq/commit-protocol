"""Regression checks for the published Studio Next lifecycle evidence contract."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_r12_evidence_ids_match_the_registered_evidence_keys() -> None:
    files = sorted((ROOT / "evidence").glob("issuer-*/r12-*.json"))
    assert files

    for path in files:
        issuer = path.parent.name.rsplit("-", 1)[-1]
        record = json.loads(path.read_text(encoding="utf-8"))
        mission_id = record["mission_id"]
        assert record["evidence_id"] == f"{mission_id}-evidence-{issuer}"
        assert record["url"].endswith(f"/{path.name}")


def test_live_proof_reuses_one_evidence_id_and_record_id_per_issuer() -> None:
    source = (ROOT / "scripts" / "live_studio_next_proof.mjs").read_text(
        encoding="utf-8",
    )
    assert 'evidenceId: `${mission.missionId}-evidence-${suffix}`' in source
    assert 'recordId: `${mission.missionId}-${suffix}`' in source
    assert "const evidenceId = record.evidenceId" in source
    assert "const recordId = record.recordId" in source
    assert "args: [mission.missionId, evidenceId]" in source
    assert "          recordId," in source


def test_live_evaluation_uses_exact_call_fee_simulation_and_requires_callback_funding() -> None:
    source = (ROOT / "scripts" / "live_studio_next_proof.mjs").read_text(
        encoding="utf-8",
    )
    assert "client.estimateTransactionFeesForWrite(call)" in source
    assert 'deriveInternalMessageCallKey("apply_decision")' in source
    assert "exact evaluation simulation returned no funded finalized apply_decision allocation" in source
