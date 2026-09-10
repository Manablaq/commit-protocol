"""Direct tests for the isolated GenLayer independent-evaluation probe."""

from pathlib import Path
import json

import pytest


ROOT = Path(__file__).resolve().parents[2]
URL_A = "https://publisher-a.example/records/mission-001"
URL_B = "https://publisher-b.example/records/mission-001"


def load_probe(vm):
    from gltest.direct import deploy_contract

    return deploy_contract(ROOT / "probes/independent_evaluation.py", vm)


def record(eligible, reason_code):
    return {
        "schema": "commit-evidence-v1",
        "eligible": eligible,
        "reason_code": reason_code,
    }


def test_independent_evidence_drives_bounded_decision(probe_vm):
    probe_vm.mock_web(URL_A, {"status": 200, "body": json.dumps(record(True, "ok"))})
    probe_vm.mock_web(URL_B, {"status": 200, "body": json.dumps(record(True, "ok"))})
    contract = load_probe(probe_vm)

    contract.evaluate(URL_A, URL_B)

    assert contract.state() == {
        "last_decision": "COMMIT",
        "last_reason_code": "all_sources_eligible",
        "evaluation_count": 1,
    }
    assert probe_vm.run_validator() is True


def test_validator_rejects_forged_leader_decision(probe_vm):
    probe_vm.mock_web(URL_A, {"status": 200, "body": json.dumps(record(True, "ok"))})
    probe_vm.mock_web(URL_B, {"status": 200, "body": json.dumps(record(True, "ok"))})
    contract = load_probe(probe_vm)
    contract.evaluate(URL_A, URL_B)

    assert probe_vm.run_validator(
        leader_result={"decision": "ABORT", "reason_code": "source_ineligible"}
    ) is False


def test_validator_rejects_changed_independent_source(probe_vm):
    probe_vm.mock_web(URL_A, {"status": 200, "body": json.dumps(record(True, "ok"))})
    probe_vm.mock_web(URL_B, {"status": 200, "body": json.dumps(record(True, "ok"))})
    contract = load_probe(probe_vm)
    contract.evaluate(URL_A, URL_B)

    probe_vm.clear_mocks()
    probe_vm.mock_web(URL_A, {"status": 200, "body": json.dumps(record(True, "ok"))})
    probe_vm.mock_web(URL_B, {"status": 200, "body": json.dumps(record(False, "revoked"))})
    assert probe_vm.run_validator() is False


@pytest.mark.parametrize(
    "a,b,error",
    [
        (URL_A, URL_A, "two distinct"),
        ("", URL_B, "two distinct"),
    ],
)
def test_invalid_source_pair_does_not_fetch_or_write(probe_vm, a, b, error):
    contract = load_probe(probe_vm)
    with pytest.raises(Exception, match=error):
        contract.evaluate(a, b)
    assert contract.state()["evaluation_count"] == 0
