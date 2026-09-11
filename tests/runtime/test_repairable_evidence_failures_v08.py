from pathlib import Path
import json

import pytest

ROOT = Path(__file__).resolve().parents[2]

MISSION_ID = "mission-repair-001"
DIGEST = (
    "983307fac383ac4a92be6c0c361ea8f3c9d9efa20ad5e6e8bc8dee932f2a6103"
)

AUTHORITY_A = "publisher-a"
AUTHORITY_B = "publisher-b"

URL_A = "https://publisher-a.example/records/mission-repair-001"
URL_B = "https://publisher-b.example/records/mission-repair-001"

RECORD_A = "record-a"
RECORD_B = "record-b"

VERSION_1 = 1
VERSION_2 = 2

PREPARE = 2_000_000_100
RECOVERY = 2_000_000_200


def create_address(byte_hex: str):
    from genlayer import Address

    return Address(bytes.fromhex(byte_hex * 20))


PRINCIPAL = bytes.fromhex("11" * 20)


def principal():
    return create_address("11")


def issuer_a():
    return create_address("21")


def issuer_b():
    return create_address("22")


def refund():
    return create_address("31")


def beneficiary():
    return create_address("41")


def load_contract(vm):
    from gltest.direct import deploy_contract

    return deploy_contract(ROOT / "contracts/commit.py", vm)


def canonical_hash(payload: dict) -> str:
    from eth_hash.auto import keccak

    encoded = json.dumps(
        payload,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")

    return keccak(encoded).hex()


def payload(eligible: bool = True) -> dict:
    return {
        "eligible": eligible,
        "reason_code": "ok" if eligible else "not_eligible",
        "effect_claims": {
            "effect-001": eligible,
        },
    }


def register_authorities(contract, probe_vm):
    probe_vm.sender = PRINCIPAL

    contract.register_authority(
        AUTHORITY_A,
        "publisher-a.example",
        "/records",
        issuer_a(),
        1,
    )

    contract.register_authority(
        AUTHORITY_B,
        "publisher-b.example",
        "/records",
        issuer_b(),
        1,
    )


def create_mission(contract, probe_vm):
    from gltest.direct import create_address

    probe_vm.warp("2033-05-18T03:33:20Z")
    probe_vm.sender = PRINCIPAL

    contract.create_mission(
        MISSION_ID,
        "Procure a verified sensor package",
        DIGEST,
        10,
        refund(),
        PREPARE,
        RECOVERY,
    )

    probe_vm.value = 10
    contract.fund_mission(MISSION_ID)
    probe_vm.value = 0

    supplier = create_address("repair-supplier")
    contract.authorize_supplier(MISSION_ID, supplier)

    probe_vm.sender = supplier

    contract.prepare_effect(
        MISSION_ID,
        "effect-001",
        "cd" * 32,
        beneficiary(),
        10,
        RECOVERY,
    )

    probe_vm.sender = PRINCIPAL


def attest(
    contract,
    probe_vm,
    *,
    authority_id: str,
    issuer,
    record_id: str,
    record_version: int,
    url: str,
    record_hash: str,
):
    probe_vm.sender = issuer

    contract.attest_evidence(
        authority_id,
        1,
        record_id,
        record_version,
        MISSION_ID,
        1,
        url,
        record_hash,
        2_000_000_001,
        RECOVERY,
    )


def prepare_sealed_mission(
    contract,
    probe_vm,
    *,
    payload_a_override=None,
):
    register_authorities(contract, probe_vm)
    create_mission(contract, probe_vm)

    payload_a = (
        payload(True)
        if payload_a_override is None
        else payload_a_override
    )
    payload_b = payload(True)

    attest(
        contract,
        probe_vm,
        authority_id=AUTHORITY_A,
        issuer=issuer_a(),
        record_id=RECORD_A,
        record_version=VERSION_1,
        url=URL_A,
        record_hash=canonical_hash(payload_a),
    )

    attest(
        contract,
        probe_vm,
        authority_id=AUTHORITY_B,
        issuer=issuer_b(),
        record_id=RECORD_B,
        record_version=VERSION_1,
        url=URL_B,
        record_hash=canonical_hash(payload_b),
    )

    probe_vm.sender = PRINCIPAL

    contract.register_evidence(
        MISSION_ID,
        "evidence-a",
        AUTHORITY_A,
        1,
        RECORD_A,
        VERSION_1,
    )

    contract.register_evidence(
        MISSION_ID,
        "evidence-b",
        AUTHORITY_B,
        1,
        RECORD_B,
        VERSION_1,
    )

    contract.seal_mission(
        MISSION_ID,
        contract.derive_effect_root(MISSION_ID),
        contract.derive_evidence_root(MISSION_ID),
    )

    return payload_a, payload_b


def valid_record(contract, evidence_id, authority_id, url, source_payload):
    mission = contract.get_mission(MISSION_ID)

    return {
        "schema": "commit-evidence-v2",
        "evidence_id": evidence_id,
        "authority_id": authority_id,
        "url": url,
        "subject": MISSION_ID,
        "expires_at": RECOVERY,
        "mission_id": MISSION_ID,
        "objective": mission["objective"],
        "policy_digest": mission["policy_digest"],
        "policy_rule": "all-evidence-and-effects-v1",
        "intent_digest": mission["intent_digest"],
        "effect_root": mission["effect_root"],
        "payload": source_payload,
    }


def mock_valid_b(contract, probe_vm, payload_b):
    probe_vm.mock_web(
        URL_B,
        {
            "status": 200,
            "body": json.dumps(
                valid_record(
                    contract,
                    "evidence-b",
                    AUTHORITY_B,
                    URL_B,
                    payload_b,
                )
            ),
        },
    )


@pytest.mark.parametrize(
    "failure_kind,expected_code",
    [
        ("http", "source_unavailable"),
        ("missing_body", "response_body_missing"),
        ("oversized", "record_too_large"),
        ("invalid_json", "invalid_json"),
        ("schema", "unsupported_schema"),
        ("snapshot", "snapshot_mismatch"),
        ("hash", "payload_hash_mismatch"),
    ],
)
def test_evidence_failure_persists_repair_required_response(
    probe_vm,
    failure_kind,
    expected_code,
):
    contract = load_contract(probe_vm)
    payload_a, payload_b = prepare_sealed_mission(contract, probe_vm)

    record_a = valid_record(
        contract,
        "evidence-a",
        AUTHORITY_A,
        URL_A,
        payload_a,
    )

    if failure_kind == "http":
        mocked_a = {"status": 503, "body": b""}
    elif failure_kind == "missing_body":
        mocked_a = {"status": 200, "body": None}
    elif failure_kind == "oversized":
        mocked_a = {"status": 200, "body": b"x" * (16 * 1024 + 1)}
    elif failure_kind == "invalid_json":
        mocked_a = {"status": 200, "body": b"{"}
    elif failure_kind == "schema":
        record_a["schema"] = "unsupported-schema"
        mocked_a = {"status": 200, "body": json.dumps(record_a)}
    elif failure_kind == "snapshot":
        record_a["objective"] = "substituted objective"
        mocked_a = {"status": 200, "body": json.dumps(record_a)}
    elif failure_kind == "hash":
        record_a["payload"] = payload(False)
        mocked_a = {"status": 200, "body": json.dumps(record_a)}
    else:
        raise AssertionError(f"unexpected failure kind: {failure_kind}")

    probe_vm.clear_mocks()
    probe_vm.mock_web(URL_A, mocked_a)
    mock_valid_b(contract, probe_vm, payload_b)

    contract.evaluate_mission(MISSION_ID)

    mission = contract.get_mission(MISSION_ID)
    failure = contract.get_evidence_failure(MISSION_ID, "evidence-a")

    assert mission["state"] == "SEALED"
    assert mission["decision"] == ""
    assert mission["decision_nonce"] == ""

    assert failure["status"] == "REPAIR_REQUIRED"
    assert failure["failure_code"] == expected_code
    assert failure["evidence_id"] == "evidence-a"
    assert failure["record_id"] == RECORD_A
    assert failure["failed_record_version"] == VERSION_1
    assert failure["mission_version"] == 1
    assert failure["attempt"] == 1


def test_valid_negative_evidence_is_abort_not_repair_failure(probe_vm):
    contract = load_contract(probe_vm)
    negative = payload(False)
    payload_a, payload_b = prepare_sealed_mission(
        contract,
        probe_vm,
        payload_a_override=negative,
    )

    probe_vm.mock_web(
        URL_A,
        {
            "status": 200,
            "body": json.dumps(
                valid_record(
                    contract,
                    "evidence-a",
                    AUTHORITY_A,
                    URL_A,
                    negative,
                )
            ),
        },
    )

    mock_valid_b(contract, probe_vm, payload_b)

    contract.evaluate_mission(MISSION_ID)

    mission = contract.get_mission(MISSION_ID)

    assert mission["decision"] == "ABORT"

    with pytest.raises(Exception, match="failure"):
        contract.get_evidence_failure(MISSION_ID, "evidence-a")


def test_repair_requires_strictly_newer_authenticated_record_version(probe_vm):
    contract = load_contract(probe_vm)
    payload_a, payload_b = prepare_sealed_mission(contract, probe_vm)

    probe_vm.mock_web(URL_A, {"status": 503, "body": b""})
    mock_valid_b(contract, probe_vm, payload_b)

    contract.evaluate_mission(MISSION_ID)

    with pytest.raises(Exception, match="newer"):
        contract.repair_evidence(
            MISSION_ID,
            "evidence-a",
            AUTHORITY_A,
            1,
            RECORD_A,
            VERSION_1,
        )


def test_repair_cannot_change_authority_or_record_identity(probe_vm):
    contract = load_contract(probe_vm)
    payload_a, payload_b = prepare_sealed_mission(contract, probe_vm)

    probe_vm.mock_web(URL_A, {"status": 503, "body": b""})
    mock_valid_b(contract, probe_vm, payload_b)

    contract.evaluate_mission(MISSION_ID)

    with pytest.raises(Exception):
        contract.repair_evidence(
            MISSION_ID,
            "evidence-a",
            AUTHORITY_B,
            1,
            RECORD_B,
            VERSION_2,
        )


def test_authenticated_successor_repair_preserves_sealed_original_and_allows_reevaluation(
    probe_vm,
):
    contract = load_contract(probe_vm)
    payload_a, payload_b = prepare_sealed_mission(contract, probe_vm)

    original_root = contract.get_mission(MISSION_ID)["evidence_root"]

    probe_vm.mock_web(URL_A, {"status": 503, "body": b""})
    mock_valid_b(contract, probe_vm, payload_b)

    contract.evaluate_mission(MISSION_ID)

    corrected_payload = payload(True)

    attest(
        contract,
        probe_vm,
        authority_id=AUTHORITY_A,
        issuer=issuer_a(),
        record_id=RECORD_A,
        record_version=VERSION_2,
        url=URL_A,
        record_hash=canonical_hash(corrected_payload),
    )

    probe_vm.sender = PRINCIPAL

    contract.repair_evidence(
        MISSION_ID,
        "evidence-a",
        AUTHORITY_A,
        1,
        RECORD_A,
        VERSION_2,
    )

    mission_after_repair = contract.get_mission(MISSION_ID)
    repair = contract.get_evidence_repair(MISSION_ID, "evidence-a")

    assert mission_after_repair["evidence_root"] == original_root
    assert repair["original_record_version"] == VERSION_1
    assert repair["active_record_version"] == VERSION_2
    assert repair["status"] == "READY"

    probe_vm.clear_mocks()

    probe_vm.mock_web(
        URL_A,
        {
            "status": 200,
            "body": json.dumps(
                valid_record(
                    contract,
                    "evidence-a",
                    AUTHORITY_A,
                    URL_A,
                    corrected_payload,
                )
            ),
        },
    )

    mock_valid_b(contract, probe_vm, payload_b)

    contract.evaluate_mission(MISSION_ID)

    mission = contract.get_mission(MISSION_ID)

    assert mission["decision"] == "COMMIT"
    assert mission["state"] == "DECISION_PENDING"


def test_repair_after_recovery_deadline_is_rejected(probe_vm):
    contract = load_contract(probe_vm)
    payload_a, payload_b = prepare_sealed_mission(contract, probe_vm)

    probe_vm.mock_web(URL_A, {"status": 503, "body": b""})
    mock_valid_b(contract, probe_vm, payload_b)

    contract.evaluate_mission(MISSION_ID)

    probe_vm.warp("2033-05-18T03:36:41Z")

    with pytest.raises(Exception, match="deadline"):
        contract.repair_evidence(
            MISSION_ID,
            "evidence-a",
            AUTHORITY_A,
            1,
            RECORD_A,
            VERSION_2,
        )


def test_validator_disagreement_is_not_persisted_as_evidence_failure(probe_vm):
    contract = load_contract(probe_vm)
    payload_a, payload_b = prepare_sealed_mission(contract, probe_vm)

    probe_vm.mock_web(
        URL_A,
        {
            "status": 200,
            "body": json.dumps(
                valid_record(
                    contract,
                    "evidence-a",
                    AUTHORITY_A,
                    URL_A,
                    payload_a,
                )
            ),
        },
    )

    mock_valid_b(contract, probe_vm, payload_b)

    contract.evaluate_mission(MISSION_ID)

    assert probe_vm.run_validator(
        leader_result={
            "decision": "ABORT",
            "reason_code": "forged",
            "mission_id": MISSION_ID,
        }
    ) is False

    with pytest.raises(Exception, match="failure"):
        contract.get_evidence_failure(MISSION_ID, "evidence-a")

def test_active_evidence_root_defaults_to_sealed_root(probe_vm):
    contract = load_contract(probe_vm)
    prepare_sealed_mission(contract, probe_vm)

    mission = contract.get_mission(MISSION_ID)
    active_root = contract.derive_active_evidence_root(
        MISSION_ID
    )

    assert active_root == mission["evidence_root"]


def test_repair_changes_active_root_without_mutating_sealed_root(
    probe_vm,
):
    contract = load_contract(probe_vm)
    payload_a, payload_b = prepare_sealed_mission(
        contract,
        probe_vm,
    )

    original_root = contract.get_mission(
        MISSION_ID
    )["evidence_root"]

    probe_vm.mock_web(
        URL_A,
        {"status": 503, "body": b""},
    )
    mock_valid_b(contract, probe_vm, payload_b)

    contract.evaluate_mission(MISSION_ID)

    attest(
        contract,
        probe_vm,
        authority_id=AUTHORITY_A,
        issuer=issuer_a(),
        record_id=RECORD_A,
        record_version=VERSION_2,
        url=URL_A,
        record_hash=canonical_hash(payload_a),
    )

    probe_vm.sender = PRINCIPAL

    contract.repair_evidence(
        MISSION_ID,
        "evidence-a",
        AUTHORITY_A,
        1,
        RECORD_A,
        VERSION_2,
    )

    mission = contract.get_mission(MISSION_ID)
    active_root = contract.derive_active_evidence_root(
        MISSION_ID
    )

    assert mission["evidence_root"] == original_root
    assert active_root != original_root


def test_repaired_successor_changes_exact_decision_commitment(
    probe_vm,
):
    from eth_hash.auto import keccak

    contract = load_contract(probe_vm)

    payload_a, payload_b = prepare_sealed_mission(
        contract,
        probe_vm,
    )

    sealed_mission = contract.get_mission(MISSION_ID)
    sealed_root = sealed_mission["evidence_root"]

    probe_vm.mock_web(
        URL_A,
        {"status": 503, "body": b""},
    )

    mock_valid_b(
        contract,
        probe_vm,
        payload_b,
    )

    contract.evaluate_mission(MISSION_ID)

    failure = contract.get_evidence_failure(
        MISSION_ID,
        "evidence-a",
    )

    assert failure["status"] == "REPAIR_REQUIRED"

    attest(
        contract,
        probe_vm,
        authority_id=AUTHORITY_A,
        issuer=issuer_a(),
        record_id=RECORD_A,
        record_version=VERSION_2,
        url=URL_A,
        record_hash=canonical_hash(payload_a),
    )

    probe_vm.sender = PRINCIPAL

    contract.repair_evidence(
        MISSION_ID,
        "evidence-a",
        AUTHORITY_A,
        1,
        RECORD_A,
        VERSION_2,
    )

    probe_vm.clear_mocks()

    probe_vm.mock_web(
        URL_A,
        {
            "status": 200,
            "body": json.dumps(
                valid_record(
                    contract,
                    "evidence-a",
                    AUTHORITY_A,
                    URL_A,
                    payload_a,
                )
            ),
        },
    )

    mock_valid_b(
        contract,
        probe_vm,
        payload_b,
    )

    contract.evaluate_mission(MISSION_ID)

    mission = contract.get_mission(MISSION_ID)

    assert mission["decision"] == "COMMIT"

    active_root = contract.derive_active_evidence_root(
        MISSION_ID
    )

    assert active_root != sealed_root

    assert (
        mission["evaluation_evidence_root"]
        == active_root
    )

    def frame(value):
        return str(len(value)) + ":" + value

    legacy_payload = (
        "commit-decision-v2"
        + frame(MISSION_ID)
        + frame(str(mission["version"]))
        + frame(mission["decision"])
        + frame(mission["reason_code"])
        + frame(mission["effect_root"])
        + frame(mission["evidence_root"])
    )

    legacy_nonce = keccak(
        legacy_payload.encode("utf-8")
    ).hex()

    assert mission["decision_nonce"] != legacy_nonce


def test_repaired_decision_receipt_exposes_exact_evaluation_evidence_root(
    probe_vm,
):
    contract = load_contract(probe_vm)

    payload_a, payload_b = prepare_sealed_mission(
        contract,
        probe_vm,
    )

    sealed_root = contract.get_mission(
        MISSION_ID
    )["evidence_root"]

    probe_vm.mock_web(
        URL_A,
        {
            "status": 503,
            "body": b"",
        },
    )

    mock_valid_b(
        contract,
        probe_vm,
        payload_b,
    )

    contract.evaluate_mission(MISSION_ID)

    failure = contract.get_evidence_failure(
        MISSION_ID,
        "evidence-a",
    )

    assert failure["status"] == "REPAIR_REQUIRED"

    attest(
        contract,
        probe_vm,
        authority_id=AUTHORITY_A,
        issuer=issuer_a(),
        record_id=RECORD_A,
        record_version=VERSION_2,
        url=URL_A,
        record_hash=canonical_hash(payload_a),
    )

    probe_vm.sender = PRINCIPAL

    contract.repair_evidence(
        MISSION_ID,
        "evidence-a",
        AUTHORITY_A,
        1,
        RECORD_A,
        VERSION_2,
    )

    active_root = contract.derive_active_evidence_root(
        MISSION_ID
    )

    assert active_root != sealed_root

    probe_vm.clear_mocks()

    probe_vm.mock_web(
        URL_A,
        {
            "status": 200,
            "body": json.dumps(
                valid_record(
                    contract,
                    "evidence-a",
                    AUTHORITY_A,
                    URL_A,
                    payload_a,
                )
            ),
        },
    )

    mock_valid_b(
        contract,
        probe_vm,
        payload_b,
    )

    contract.evaluate_mission(MISSION_ID)

    mission = contract.get_mission(MISSION_ID)

    assert mission["decision"] == "COMMIT"
    assert (
        mission["evaluation_evidence_root"]
        == active_root
    )

    receipt = contract.get_mission_receipt(
        MISSION_ID
    )

    assert receipt["evidence_root"] == sealed_root
    assert (
        receipt["evaluation_evidence_root"]
        == active_root
    )


def test_repaired_decision_manifest_exposes_exact_evaluation_evidence_root(
    probe_vm,
):
    contract = load_contract(probe_vm)

    payload_a, payload_b = prepare_sealed_mission(
        contract,
        probe_vm,
    )

    sealed_root = contract.get_mission(
        MISSION_ID
    )["evidence_root"]

    probe_vm.mock_web(
        URL_A,
        {
            "status": 503,
            "body": b"",
        },
    )

    mock_valid_b(
        contract,
        probe_vm,
        payload_b,
    )

    contract.evaluate_mission(MISSION_ID)

    failure = contract.get_evidence_failure(
        MISSION_ID,
        "evidence-a",
    )

    assert failure["status"] == "REPAIR_REQUIRED"

    attest(
        contract,
        probe_vm,
        authority_id=AUTHORITY_A,
        issuer=issuer_a(),
        record_id=RECORD_A,
        record_version=VERSION_2,
        url=URL_A,
        record_hash=canonical_hash(payload_a),
    )

    probe_vm.sender = PRINCIPAL

    contract.repair_evidence(
        MISSION_ID,
        "evidence-a",
        AUTHORITY_A,
        1,
        RECORD_A,
        VERSION_2,
    )

    active_root = contract.derive_active_evidence_root(
        MISSION_ID
    )

    assert active_root != sealed_root

    probe_vm.clear_mocks()

    probe_vm.mock_web(
        URL_A,
        {
            "status": 200,
            "body": json.dumps(
                valid_record(
                    contract,
                    "evidence-a",
                    AUTHORITY_A,
                    URL_A,
                    payload_a,
                )
            ),
        },
    )

    mock_valid_b(
        contract,
        probe_vm,
        payload_b,
    )

    contract.evaluate_mission(MISSION_ID)

    mission = contract.get_mission(MISSION_ID)

    assert mission["decision"] == "COMMIT"
    assert (
        mission["evaluation_evidence_root"]
        == active_root
    )

    manifest = contract.get_mission_manifest(
        MISSION_ID
    )

    assert manifest["evidence_root"] == sealed_root
    assert (
        manifest["evaluation_evidence_root"]
        == active_root
    )
