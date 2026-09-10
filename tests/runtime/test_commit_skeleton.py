"""Direct-runtime checks for the deterministic escrow coordinator."""

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
DIGEST = "ab" * 32
OBJECTIVE = "Procure a verified sensor package"
REFUND_LABEL = "refund-beneficiary"
FUTURE_PREPARE = 3_000_000_000
FUTURE_RECOVERY = 3_000_000_100
PRINCIPAL = bytes.fromhex("11" * 20)
AUTHORITY_A = "publisher-a"
AUTHORITY_B = "publisher-b"


def load_contract(vm):
    from gltest.direct import deploy_contract
    return deploy_contract(ROOT / "contracts/commit.py", vm)


def create_default(
    contract, probe_vm, *, prepare=FUTURE_PREPARE, recovery=FUTURE_RECOVERY, budget=10
):
    from gltest.direct import create_address

    contract.register_authority(AUTHORITY_A, "publisher-a.example", "/records")
    contract.register_authority(AUTHORITY_B, "publisher-b.example", "/records")
    contract.create_mission(
        "mission-001",
        OBJECTIVE,
        DIGEST,
        budget,
        create_address(REFUND_LABEL),
        prepare,
        recovery,
    )
    # Payable funding is a distinct lifecycle step. The helper funds the
    # default fixture so tests that reach sealing exercise a fully collateralized
    # mission; dedicated tests cover underfunding and overfunding.
    probe_vm.sender = PRINCIPAL
    probe_vm.value = budget
    contract.fund_mission("mission-001")
    probe_vm.value = 0


def add_default_evidence(contract, probe_vm, *, recovery=FUTURE_RECOVERY):
    probe_vm.sender = PRINCIPAL
    contract.register_evidence(
        "mission-001", "evidence-001", AUTHORITY_A,
        "https://publisher-a.example/records/mission-001",
        "12" * 32, "mission-001", recovery,
    )
    contract.register_evidence(
        "mission-001", "evidence-002", AUTHORITY_B,
        "https://publisher-b.example/records/mission-001",
        "34" * 32, "mission-001", recovery,
    )


def add_evaluable_evidence(contract, probe_vm, eligible_a=True, eligible_b=True):
    import json
    from eth_hash.auto import keccak

    records = [
        ("evidence-001", AUTHORITY_A, "https://publisher-a.example/records/mission-001", eligible_a),
        ("evidence-002", AUTHORITY_B, "https://publisher-b.example/records/mission-001", eligible_b),
    ]
    probe_vm.sender = PRINCIPAL
    for evidence_id, authority_id, url, eligible in records:
        payload = {"eligible": eligible, "reason_code": "ok" if eligible else "revoked"}
        canonical_payload = json.dumps(
            payload, ensure_ascii=True, sort_keys=True, separators=(",", ":")
        )
        record_hash = keccak(canonical_payload.encode("utf-8")).hex()
        contract.register_evidence(
            "mission-001", evidence_id, authority_id, url, record_hash,
            "mission-001", FUTURE_RECOVERY,
        )
        probe_vm.mock_web(url, {
            "status": 200,
            "body": json.dumps({
                "schema": "commit-evidence-v1",
                "evidence_id": evidence_id,
                "authority_id": authority_id,
                "url": url,
                "subject": "mission-001",
                "expires_at": FUTURE_RECOVERY,
                "payload": payload,
            }),
        })


def seal_evaluable_mission(contract, probe_vm, eligible_a=True, eligible_b=True):
    from gltest.direct import create_address

    create_default(contract, probe_vm, budget=10)
    probe_vm.sender = create_address("supplier")
    contract.prepare_effect(
        "mission-001", "effect-001", "cd" * 32, create_address("beneficiary"),
        7, FUTURE_RECOVERY,
    )
    add_evaluable_evidence(contract, probe_vm, eligible_a, eligible_b)
    contract.seal_mission(
        "mission-001", contract.derive_effect_root("mission-001"),
        contract.derive_evidence_root("mission-001"),
    )


def test_protocol_discloses_custody_and_evaluation(probe_vm):
    contract = load_contract(probe_vm)
    assert contract.protocol_info() == {
        "protocol": "commit",
        "revision": "0.4.0-semantic-escrow",
        "custody_enabled": True,
        "semantic_evaluation_enabled": True,
        "mission_count": 0,
        "external_withdrawal_recovery": False,
    }


def test_authority_registry_is_owner_only_and_immutable(probe_vm):
    contract = load_contract(probe_vm)
    contract.register_authority("publisher-a", "publisher-a.example", "/records")
    assert contract.get_authority("publisher-a") == {
        "authority_id": "publisher-a",
        "host": "publisher-a.example",
        "path_prefix": "/records",
    }
    from gltest.direct import create_address

    probe_vm.sender = create_address("outsider")
    with pytest.raises(Exception, match="owner required"):
        contract.register_authority("publisher-b", "publisher-b.example", "/records")

    probe_vm.sender = PRINCIPAL
    with pytest.raises(Exception, match="authority already exists"):
        contract.register_authority("publisher-a", "changed.example", "/other")


def test_create_mission_binds_principal_and_immutable_inputs(probe_vm):
    contract = load_contract(probe_vm)
    create_default(contract, probe_vm)
    from gltest.direct import create_address
    from spec_model.onchain import intent_digest

    mission = contract.get_mission("mission-001")
    assert mission["mission_id"] == "mission-001"
    assert mission["principal"] == "0x" + "11" * 20
    assert mission["state"] == "PREPARING"
    assert mission["version"] == 1
    assert mission["objective"] == OBJECTIVE
    assert mission["policy_digest"] == DIGEST
    assert mission["intent_digest"] == contract.derive_intent_digest("mission-001")
    assert mission["intent_digest"] == intent_digest(
        mission_id="mission-001",
        objective=OBJECTIVE,
        policy_digest=DIGEST,
        budget=10,
        refund_beneficiary=create_address(REFUND_LABEL).as_hex,
        prepare_deadline=FUTURE_PREPARE,
        recovery_deadline=FUTURE_RECOVERY,
    )
    assert mission["effect_root"] == ""
    assert mission["evidence_root"] == ""
    assert mission["prepare_deadline"] == FUTURE_PREPARE
    assert mission["recovery_deadline"] == FUTURE_RECOVERY
    assert mission["budget"] == 10
    assert mission["prepared_value"] == 0
    assert mission["refund_beneficiary"] != "0x" + "00" * 20
    assert mission["evidence_count"] == 0
    assert contract.protocol_info()["mission_count"] == 1


@pytest.mark.parametrize(
    "mission_id,objective,policy,budget,prepare,recovery,error",
    [
        ("", OBJECTIVE, DIGEST, 10, 100, 200, "invalid mission id"),
        ("m:x", OBJECTIVE, DIGEST, 10, 100, 200, "invalid mission id"),
        ("m", OBJECTIVE, "AB" * 32, 10, 100, 200, "policy digest"),
        ("m", OBJECTIVE, "ab" * 31, 10, 100, 200, "policy digest"),
        ("m", OBJECTIVE, DIGEST, 0, 100, 200, "budget"),
        ("m", OBJECTIVE, DIGEST, 10, 0, 200, "deadline"),
        ("m", OBJECTIVE, DIGEST, 10, 200, 200, "deadline"),
        ("m", OBJECTIVE, DIGEST, 10, 201, 200, "deadline"),
        ("m", "Café", DIGEST, 10, 100, 200, "objective"),
    ],
)
def test_invalid_creation_is_rejected(
    probe_vm, mission_id, objective, policy, budget, prepare, recovery, error
):
    contract = load_contract(probe_vm)
    from gltest.direct import create_address

    with pytest.raises(Exception, match=error):
        contract.create_mission(
            mission_id,
            objective,
            policy,
            budget,
            create_address(REFUND_LABEL),
            prepare,
            recovery,
        )
    assert contract.protocol_info()["mission_count"] == 0


def test_payable_funding_is_bounded_and_recorded(probe_vm):
    contract = load_contract(probe_vm)
    from gltest.direct import create_address

    contract.create_mission(
        "mission-001", OBJECTIVE, DIGEST, 10, create_address(REFUND_LABEL),
        FUTURE_PREPARE, FUTURE_RECOVERY,
    )
    probe_vm.sender = PRINCIPAL
    probe_vm.value = 7
    contract.fund_mission("mission-001")
    assert contract.get_mission("mission-001")["funded_value"] == 7

    probe_vm.value = 4
    with pytest.raises(Exception, match="funding exceeds mission budget"):
        contract.fund_mission("mission-001")
    probe_vm.value = 0
    assert contract.get_mission("mission-001")["funded_value"] == 7


def test_zero_and_late_funding_are_rejected_without_mutation(probe_vm):
    contract = load_contract(probe_vm)
    from gltest.direct import create_address

    probe_vm.warp("1970-01-01T00:00:50Z")
    contract.create_mission(
        "mission-001", OBJECTIVE, DIGEST, 10, create_address(REFUND_LABEL),
        100, 200,
    )
    probe_vm.sender = PRINCIPAL
    with pytest.raises(Exception, match="funding value must be positive"):
        contract.fund_mission("mission-001")
    probe_vm.warp("1970-01-01T00:01:41Z")
    probe_vm.value = 1
    with pytest.raises(Exception, match="preparation deadline has passed"):
        contract.fund_mission("mission-001")
    probe_vm.value = 0
    assert contract.get_mission("mission-001")["funded_value"] == 0


def test_duplicate_mission_is_rejected_without_mutation(probe_vm):
    contract = load_contract(probe_vm)
    create_default(contract, probe_vm)
    with pytest.raises(Exception, match="mission already exists"):
        from gltest.direct import create_address

        contract.create_mission(
            "mission-001", "different", "cd" * 32, 5,
            create_address("other-refund"), 300, 400,
        )
    mission = contract.get_mission("mission-001")
    assert mission["objective"] == OBJECTIVE
    assert mission["policy_digest"] == DIGEST
    assert mission["prepare_deadline"] == FUTURE_PREPARE
    assert contract.protocol_info()["mission_count"] == 1


def test_unknown_mission_is_rejected(probe_vm):
    contract = load_contract(probe_vm)
    with pytest.raises(Exception, match="mission not found"):
        contract.get_mission("absent")


def test_supplier_prepares_effect_and_principal_seals_snapshot(probe_vm):
    contract = load_contract(probe_vm)
    create_default(contract, probe_vm, budget=10)
    from gltest.direct import create_address

    supplier = create_address("supplier")
    beneficiary = create_address("beneficiary")
    probe_vm.sender = supplier
    contract.prepare_effect(
        "mission-001", "effect-001", "cd" * 32, beneficiary, 7, FUTURE_RECOVERY
    )
    effect = contract.get_effect("mission-001", "effect-001")
    assert effect["mission_id"] == "mission-001"
    assert effect["effect_id"] == "effect-001"
    assert effect["supplier"] == supplier.as_hex
    assert effect["digest"] == "cd" * 32
    assert effect["beneficiary"] == beneficiary.as_hex
    assert effect["value"] == 7
    assert effect["expiry"] == FUTURE_RECOVERY
    assert contract.get_mission("mission-001")["prepared_value"] == 7

    from spec_model.onchain import effect_root
    assert contract.derive_effect_root("mission-001") == effect_root([effect])

    add_default_evidence(contract, probe_vm)
    evidence = contract.get_evidence("mission-001", "evidence-001")
    assert evidence["authority_id"] == AUTHORITY_A
    assert evidence["subject"] == "mission-001"
    from spec_model.provenance import evidence_root
    assert contract.derive_evidence_root("mission-001") == evidence_root([
        evidence,
        contract.get_evidence("mission-001", "evidence-002"),
    ])

    probe_vm.sender = PRINCIPAL
    effect_root = contract.derive_effect_root("mission-001")
    contract.seal_mission(
        "mission-001", effect_root, contract.derive_evidence_root("mission-001")
    )
    mission = contract.get_mission("mission-001")
    assert mission["state"] == "SEALED"
    assert mission["effect_count"] == 1
    assert mission["effect_root"] == effect_root
    assert mission["evidence_root"] == contract.derive_evidence_root("mission-001")


def test_seal_rejects_underfunded_effects(probe_vm):
    contract = load_contract(probe_vm)
    from gltest.direct import create_address

    contract.register_authority(AUTHORITY_A, "publisher-a.example", "/records")
    contract.register_authority(AUTHORITY_B, "publisher-b.example", "/records")
    contract.create_mission(
        "mission-001", OBJECTIVE, DIGEST, 10, create_address(REFUND_LABEL),
        FUTURE_PREPARE, FUTURE_RECOVERY,
    )
    probe_vm.sender = create_address("supplier")
    contract.prepare_effect(
        "mission-001", "effect-001", "cd" * 32, create_address("beneficiary"),
        7, FUTURE_RECOVERY,
    )
    add_default_evidence(contract, probe_vm)
    with pytest.raises(Exception, match="mission is underfunded"):
        contract.seal_mission(
            "mission-001", contract.derive_effect_root("mission-001"),
            contract.derive_evidence_root("mission-001"),
        )


def test_effect_and_cancel_are_locked_after_seal(probe_vm):
    contract = load_contract(probe_vm)
    create_default(contract, probe_vm, budget=10)
    from gltest.direct import create_address

    beneficiary = create_address("beneficiary")
    contract.prepare_effect(
        "mission-001", "effect-001", "cd" * 32, beneficiary, 7, FUTURE_RECOVERY
    )
    add_default_evidence(contract, probe_vm)
    contract.seal_mission(
        "mission-001", contract.derive_effect_root("mission-001"),
        contract.derive_evidence_root("mission-001"),
    )
    with pytest.raises(Exception, match="mission is not preparing"):
        contract.prepare_effect("mission-001", "effect-002", "34" * 32, beneficiary, 2, 150)
    with pytest.raises(Exception, match="sealed mission"):
        contract.cancel_mission("mission-001")


def test_seal_rejects_effect_root_that_does_not_match(probe_vm):
    contract = load_contract(probe_vm)
    create_default(contract, probe_vm, budget=10)
    from gltest.direct import create_address

    contract.prepare_effect(
        "mission-001", "effect-001", "cd" * 32, create_address("beneficiary"),
        7, FUTURE_RECOVERY,
    )
    add_default_evidence(contract, probe_vm)
    with pytest.raises(Exception, match="effect root does not match"):
        contract.seal_mission(
            "mission-001", "ef" * 32, contract.derive_evidence_root("mission-001")
        )
    mission = contract.get_mission("mission-001")
    assert mission["state"] == "PREPARING"
    assert mission["effect_root"] == ""
    assert mission["evidence_root"] == ""


def test_evidence_url_and_subject_are_bound_before_seal(probe_vm):
    contract = load_contract(probe_vm)
    create_default(contract, probe_vm, budget=10)

    invalid = [
        ("outside", "https://publisher-a.example.evil/records/mission-001", "outside authority"),
        ("prefix", "https://publisher-a.example/records-other/mission-001", "outside authority"),
        ("query", "https://publisher-a.example/records/mission-001?x=1", "outside authority"),
        ("subject", "https://publisher-a.example/records/mission-001", "subject mismatch"),
    ]
    for evidence_id, url, error in invalid:
        with pytest.raises(Exception, match=error):
            contract.register_evidence(
                "mission-001", evidence_id, AUTHORITY_A, url,
                "12" * 32, "other-mission" if evidence_id == "subject" else "mission-001",
                FUTURE_RECOVERY,
            )
    assert contract.get_mission("mission-001")["evidence_count"] == 0


def test_seal_requires_distinct_registered_evidence_authorities(probe_vm):
    contract = load_contract(probe_vm)
    create_default(contract, probe_vm, budget=10)
    from gltest.direct import create_address

    contract.prepare_effect(
        "mission-001", "effect-001", "cd" * 32, create_address("beneficiary"),
        7, FUTURE_RECOVERY,
    )
    contract.register_evidence(
        "mission-001", "evidence-001", AUTHORITY_A,
        "https://publisher-a.example/records/mission-001/a", "12" * 32,
        "mission-001", FUTURE_RECOVERY,
    )
    contract.register_evidence(
        "mission-001", "evidence-002", AUTHORITY_A,
        "https://publisher-a.example/records/mission-001/b", "34" * 32,
        "mission-001", FUTURE_RECOVERY,
    )
    with pytest.raises(Exception, match="authorities must be distinct"):
        contract.seal_mission(
            "mission-001", contract.derive_effect_root("mission-001"),
            contract.derive_evidence_root("mission-001"),
        )


def test_evaluation_reaches_commit_only_when_all_sources_are_eligible(probe_vm):
    contract = load_contract(probe_vm)
    seal_evaluable_mission(contract, probe_vm, True, True)

    contract.evaluate_mission("mission-001")

    mission = contract.get_mission("mission-001")
    assert mission["decision"] == "COMMIT"
    assert mission["reason_code"] == "all_sources_eligible"
    assert mission["state"] == "DECISION_PENDING"
    assert mission["allocation_applied"] is False
    assert mission["evaluation_count"] == 1
    assert probe_vm.run_validator() is True

    from genlayer import gl

    probe_vm.sender = gl.message.contract_address
    contract.apply_decision("mission-001", mission["decision_nonce"])
    assert contract.get_mission("mission-001")["state"] == "COMMITTED"


def test_finalized_allocation_credits_effect_and_refund_entitlements(probe_vm):
    contract = load_contract(probe_vm)
    seal_evaluable_mission(contract, probe_vm, True, True)
    contract.evaluate_mission("mission-001")
    mission = contract.get_mission("mission-001")
    from genlayer import gl

    probe_vm.sender = gl.message.contract_address
    contract.apply_decision("mission-001", mission["decision_nonce"])
    effect = contract.get_effect("mission-001", "effect-001")
    from gltest.direct import create_address

    assert contract.get_claimable(create_address("beneficiary")) == 7
    assert contract.get_claimable(create_address(REFUND_LABEL)) == 3
    assert contract.get_mission("mission-001")["allocation_applied"] is True
    assert effect["beneficiary"] != "0x" + "00" * 20


def test_decision_callback_requires_exact_nonce_and_is_idempotent(probe_vm):
    contract = load_contract(probe_vm)
    seal_evaluable_mission(contract, probe_vm, True, True)
    contract.evaluate_mission("mission-001")
    mission = contract.get_mission("mission-001")
    from genlayer import gl
    from gltest.direct import create_address

    probe_vm.sender = gl.message.contract_address
    with pytest.raises(Exception, match="decision nonce mismatch"):
        contract.apply_decision("mission-001", "00" * 32)
    contract.apply_decision("mission-001", mission["decision_nonce"])
    contract.apply_decision("mission-001", mission["decision_nonce"])
    assert contract.get_claimable(create_address("beneficiary")) == 7


def test_recovery_wins_against_a_late_decision_callback(probe_vm):
    contract = load_contract(probe_vm)
    seal_evaluable_mission(contract, probe_vm, True, True)
    contract.evaluate_mission("mission-001")
    mission = contract.get_mission("mission-001")
    from genlayer import gl
    from gltest.direct import create_address

    probe_vm.warp("2065-01-24T05:21:41Z")
    probe_vm.sender = create_address("recovery-keeper")
    contract.expire_mission("mission-001")
    assert contract.get_mission("mission-001")["state"] == "ABORTED"
    assert contract.get_claimable(create_address(REFUND_LABEL)) == 10

    probe_vm.sender = gl.message.contract_address
    contract.apply_decision("mission-001", mission["decision_nonce"])
    assert contract.get_mission("mission-001")["state"] == "ABORTED"
    assert contract.get_claimable(create_address(REFUND_LABEL)) == 10


def test_claim_dispatch_consumes_one_entitlement_and_records_withdrawal(probe_vm):
    contract = load_contract(probe_vm)
    seal_evaluable_mission(contract, probe_vm, True, True)
    contract.evaluate_mission("mission-001")
    mission = contract.get_mission("mission-001")
    from genlayer import gl
    from gltest.direct import create_address

    probe_vm.sender = gl.message.contract_address
    contract.apply_decision("mission-001", mission["decision_nonce"])
    beneficiary = create_address("beneficiary")
    probe_vm.sender = beneficiary
    contract.claim_mission("mission-001")
    assert contract.get_claimable(beneficiary) == 0
    assert contract.get_withdrawal("0") == {
        "withdrawal_id": "0",
        "mission_id": "mission-001",
        "beneficiary": beneficiary.as_hex,
        "amount": 7,
        "status": "DISPATCHED",
    }
    with pytest.raises(Exception, match="no claimable balance"):
        contract.claim_mission("mission-001")


def test_evaluation_aborts_when_one_source_is_ineligible(probe_vm):
    contract = load_contract(probe_vm)
    seal_evaluable_mission(contract, probe_vm, True, False)

    contract.evaluate_mission("mission-001")

    mission = contract.get_mission("mission-001")
    assert mission["decision"] == "ABORT"
    assert mission["reason_code"] == "source_ineligible"
    assert mission["state"] == "DECISION_PENDING"
    from genlayer import gl

    probe_vm.sender = gl.message.contract_address
    contract.apply_decision("mission-001", mission["decision_nonce"])
    assert contract.get_mission("mission-001")["state"] == "ABORTED"


def test_evaluation_validator_rejects_forged_decision_and_changed_source(probe_vm):
    contract = load_contract(probe_vm)
    seal_evaluable_mission(contract, probe_vm, True, True)
    contract.evaluate_mission("mission-001")

    assert probe_vm.run_validator(
        leader_result={"decision": "ABORT", "reason_code": "source_ineligible"}
    ) is False

    import json

    probe_vm.clear_mocks()
    probe_vm.mock_web(
        "https://publisher-a.example/records/mission-001",
        {"status": 200, "body": json.dumps({"schema": "wrong"})},
    )
    assert probe_vm.run_validator() is False


def test_evaluation_is_single_use_and_only_accepts_sealed_missions(probe_vm):
    contract = load_contract(probe_vm)
    with pytest.raises(Exception, match="mission not found"):
        contract.evaluate_mission("absent")

    seal_evaluable_mission(contract, probe_vm)
    contract.evaluate_mission("mission-001")
    with pytest.raises(Exception, match="mission is not sealed"):
        contract.evaluate_mission("mission-001")


def test_effect_root_binds_all_effects_in_preparation_order(probe_vm):
    contract = load_contract(probe_vm)
    create_default(contract, probe_vm, budget=10)
    from gltest.direct import create_address

    contract.prepare_effect(
        "mission-001", "effect-001", "cd" * 32, create_address("beneficiary-a"),
        7, FUTURE_RECOVERY,
    )
    first_root = contract.derive_effect_root("mission-001")
    contract.prepare_effect(
        "mission-001", "effect-002", "34" * 32, create_address("beneficiary-b"),
        2, FUTURE_RECOVERY + 50,
    )
    second_root = contract.derive_effect_root("mission-001")
    assert first_root != second_root
    add_default_evidence(contract, probe_vm)
    contract.seal_mission(
        "mission-001", second_root, contract.derive_evidence_root("mission-001")
    )
    assert contract.get_mission("mission-001")["effect_count"] == 2


def test_only_principal_can_seal_or_cancel(probe_vm):
    contract = load_contract(probe_vm)
    create_default(contract, probe_vm, budget=10)
    from gltest.direct import create_address

    probe_vm.sender = create_address("outsider")
    with pytest.raises(Exception, match="principal required"):
        contract.seal_mission(
            "mission-001", contract.derive_effect_root("mission-001"), "12" * 32
        )
    with pytest.raises(Exception, match="principal required"):
        contract.cancel_mission("mission-001")


def test_cannot_seal_without_prepared_effect(probe_vm):
    contract = load_contract(probe_vm)
    create_default(contract, probe_vm, budget=10)
    with pytest.raises(Exception, match="no prepared effects"):
        contract.seal_mission("mission-001", "ef" * 32, "12" * 32)


@pytest.mark.parametrize(
    "effect_id,digest,value,expiry,error",
    [
        ("", "cd" * 32, 7, 150, "effect id"),
        ("effect:x", "cd" * 32, 7, 200, "effect id"),
        ("effect", "CD" * 32, 7, 150, "effect digest"),
        ("effect", "cd" * 32, 0, 150, "effect value"),
        ("effect", "cd" * 32, 7, 0, "effect expiry"),
        ("effect", "cd" * 32, 7, 150, "effect expiry"),
    ],
)
def test_invalid_effect_is_rejected(probe_vm, effect_id, digest, value, expiry, error):
    contract = load_contract(probe_vm)
    probe_vm.warp("1970-01-01T00:00:50Z")
    create_default(contract, probe_vm, prepare=100, recovery=200, budget=10)
    from gltest.direct import create_address

    with pytest.raises(Exception, match=error):
        contract.prepare_effect(
            "mission-001", effect_id, digest, create_address("beneficiary"), value, expiry
        )
    assert contract.get_mission("mission-001")["effect_count"] == 0


def test_duplicate_effect_does_not_mutate_original(probe_vm):
    contract = load_contract(probe_vm)
    create_default(contract, probe_vm, budget=10)
    from gltest.direct import create_address

    beneficiary = create_address("beneficiary")
    contract.prepare_effect(
        "mission-001", "effect-001", "cd" * 32, beneficiary, 7, FUTURE_RECOVERY
    )
    with pytest.raises(Exception, match="effect already exists"):
        contract.prepare_effect("mission-001", "effect-001", "34" * 32, beneficiary, 99, 199)
    effect = contract.get_effect("mission-001", "effect-001")
    assert effect["digest"] == "cd" * 32
    assert effect["value"] == 7
    assert contract.get_mission("mission-001")["effect_count"] == 1


def test_prepared_effects_cannot_exceed_declared_budget(probe_vm):
    contract = load_contract(probe_vm)
    create_default(contract, probe_vm, budget=7)
    from gltest.direct import create_address

    contract.prepare_effect(
        "mission-001", "effect-001", "cd" * 32, create_address("beneficiary-a"),
        7, FUTURE_RECOVERY,
    )
    with pytest.raises(Exception, match="exceed mission budget"):
        contract.prepare_effect(
            "mission-001", "effect-002", "34" * 32, create_address("beneficiary-b"),
            1, FUTURE_RECOVERY,
        )
    mission = contract.get_mission("mission-001")
    assert mission["prepared_value"] == 7
    assert mission["effect_count"] == 1


def test_preparation_deadline_blocks_late_effects_without_mutation(probe_vm):
    probe_vm.warp("1970-01-01T00:00:50Z")
    contract = load_contract(probe_vm)
    create_default(contract, probe_vm, prepare=100, recovery=200, budget=10)
    probe_vm.warp("1970-01-01T00:01:41Z")
    from gltest.direct import create_address

    with pytest.raises(Exception, match="preparation deadline"):
        contract.prepare_effect(
            "mission-001", "effect-001", "cd" * 32, create_address("beneficiary"),
            7, 200,
        )
    assert contract.get_mission("mission-001")["effect_count"] == 0


def test_anyone_can_recover_after_recovery_deadline(probe_vm):
    probe_vm.warp("1970-01-01T00:00:50Z")
    contract = load_contract(probe_vm)
    create_default(contract, probe_vm, prepare=100, recovery=200, budget=10)
    from gltest.direct import create_address

    contract.prepare_effect(
        "mission-001", "effect-001", "cd" * 32, create_address("beneficiary"),
        7, 200,
    )
    probe_vm.sender = create_address("outsider")
    with pytest.raises(Exception, match="deadline has not passed"):
        contract.expire_mission("mission-001")
    probe_vm.warp("1970-01-01T00:03:20Z")
    contract.expire_mission("mission-001")
    assert contract.get_mission("mission-001")["state"] == "ABORTED"
    with pytest.raises(Exception, match="already terminal"):
        contract.expire_mission("mission-001")


def test_expiry_can_abort_a_sealed_mission(probe_vm):
    probe_vm.warp("1970-01-01T00:00:50Z")
    contract = load_contract(probe_vm)
    create_default(contract, probe_vm, prepare=100, recovery=200, budget=10)
    from gltest.direct import create_address

    contract.prepare_effect(
        "mission-001", "effect-001", "cd" * 32, create_address("beneficiary"), 7, 200
    )
    add_default_evidence(contract, probe_vm, recovery=200)
    contract.seal_mission(
        "mission-001", contract.derive_effect_root("mission-001"),
        contract.derive_evidence_root("mission-001"),
    )
    probe_vm.warp("1970-01-01T00:03:20Z")
    contract.expire_mission("mission-001")
    assert contract.get_mission("mission-001")["state"] == "ABORTED"
