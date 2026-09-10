"""Direct-runtime checks for the deterministic, non-custodial skeleton."""

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
DIGEST = "ab" * 32


def load_contract(vm):
    from gltest.direct import deploy_contract
    return deploy_contract(ROOT / "contracts/commit.py", vm)


def test_protocol_discloses_disabled_custody_and_evaluation(probe_vm):
    contract = load_contract(probe_vm)
    assert contract.protocol_info() == {
        "protocol": "commit",
        "revision": "0.1.0-skeleton",
        "custody_enabled": False,
        "semantic_evaluation_enabled": False,
        "mission_count": 0,
    }


def test_create_mission_binds_principal_and_immutable_inputs(probe_vm):
    contract = load_contract(probe_vm)
    contract.create_mission("mission-001", DIGEST, 100, 200)
    mission = contract.get_mission("mission-001")
    assert mission["mission_id"] == "mission-001"
    assert mission["principal"] == "0x" + "11" * 20
    assert mission["state"] == "PREPARING"
    assert mission["version"] == 1
    assert mission["intent_digest"] == DIGEST
    assert mission["effect_root"] == ""
    assert mission["evidence_root"] == ""
    assert mission["prepare_deadline"] == 100
    assert mission["recovery_deadline"] == 200
    assert contract.protocol_info()["mission_count"] == 1


@pytest.mark.parametrize(
    "mission_id,digest,prepare,recovery,error",
    [
        ("", DIGEST, 100, 200, "invalid mission id"),
        ("m:x", DIGEST, 100, 200, "invalid mission id"),
        ("m", "AB" * 32, 100, 200, "intent digest"),
        ("m", "ab" * 31, 100, 200, "intent digest"),
        ("m", DIGEST, 0, 200, "deadline"),
        ("m", DIGEST, 200, 200, "deadline"),
        ("m", DIGEST, 201, 200, "deadline"),
    ],
)
def test_invalid_creation_is_rejected(probe_vm, mission_id, digest, prepare, recovery, error):
    contract = load_contract(probe_vm)
    with pytest.raises(Exception, match=error):
        contract.create_mission(mission_id, digest, prepare, recovery)
    assert contract.protocol_info()["mission_count"] == 0


def test_duplicate_mission_is_rejected_without_mutation(probe_vm):
    contract = load_contract(probe_vm)
    contract.create_mission("mission-001", DIGEST, 100, 200)
    with pytest.raises(Exception, match="mission already exists"):
        contract.create_mission("mission-001", "cd" * 32, 300, 400)
    mission = contract.get_mission("mission-001")
    assert mission["intent_digest"] == DIGEST
    assert mission["prepare_deadline"] == 100
    assert contract.protocol_info()["mission_count"] == 1


def test_unknown_mission_is_rejected(probe_vm):
    contract = load_contract(probe_vm)
    with pytest.raises(Exception, match="mission not found"):
        contract.get_mission("absent")


def test_supplier_prepares_effect_and_principal_seals_snapshot(probe_vm):
    contract = load_contract(probe_vm)
    contract.create_mission("mission-001", DIGEST, 100, 200)
    from gltest.direct import create_address

    supplier = create_address("supplier")
    beneficiary = create_address("beneficiary")
    probe_vm.sender = supplier
    contract.prepare_effect("mission-001", "effect-001", "cd" * 32, beneficiary, 7, 200)
    effect = contract.get_effect("mission-001", "effect-001")
    assert effect["mission_id"] == "mission-001"
    assert effect["effect_id"] == "effect-001"
    assert effect["supplier"] == supplier.as_hex
    assert effect["digest"] == "cd" * 32
    assert effect["beneficiary"] == beneficiary.as_hex
    assert effect["value"] == 7
    assert effect["expiry"] == 200

    probe_vm.sender = bytes.fromhex("11" * 20)
    effect_root = contract.derive_effect_root("mission-001")
    contract.seal_mission("mission-001", effect_root, "12" * 32)
    mission = contract.get_mission("mission-001")
    assert mission["state"] == "SEALED"
    assert mission["effect_count"] == 1
    assert mission["effect_root"] == effect_root
    assert mission["evidence_root"] == "12" * 32


def test_effect_and_cancel_are_locked_after_seal(probe_vm):
    contract = load_contract(probe_vm)
    contract.create_mission("mission-001", DIGEST, 100, 200)
    from gltest.direct import create_address

    beneficiary = create_address("beneficiary")
    contract.prepare_effect("mission-001", "effect-001", "cd" * 32, beneficiary, 7, 200)
    contract.seal_mission("mission-001", contract.derive_effect_root("mission-001"), "12" * 32)
    with pytest.raises(Exception, match="mission is not preparing"):
        contract.prepare_effect("mission-001", "effect-002", "34" * 32, beneficiary, 2, 150)
    with pytest.raises(Exception, match="sealed mission"):
        contract.cancel_mission("mission-001")


def test_seal_rejects_effect_root_that_does_not_match(probe_vm):
    contract = load_contract(probe_vm)
    contract.create_mission("mission-001", DIGEST, 100, 200)
    from gltest.direct import create_address

    contract.prepare_effect(
        "mission-001", "effect-001", "cd" * 32, create_address("beneficiary"), 7, 200
    )
    with pytest.raises(Exception, match="effect root does not match"):
        contract.seal_mission("mission-001", "ef" * 32, "12" * 32)
    mission = contract.get_mission("mission-001")
    assert mission["state"] == "PREPARING"
    assert mission["effect_root"] == ""
    assert mission["evidence_root"] == ""


def test_effect_root_binds_all_effects_in_preparation_order(probe_vm):
    contract = load_contract(probe_vm)
    contract.create_mission("mission-001", DIGEST, 100, 200)
    from gltest.direct import create_address

    contract.prepare_effect(
        "mission-001", "effect-001", "cd" * 32, create_address("beneficiary-a"), 7, 200
    )
    first_root = contract.derive_effect_root("mission-001")
    contract.prepare_effect(
        "mission-001", "effect-002", "34" * 32, create_address("beneficiary-b"), 2, 250
    )
    second_root = contract.derive_effect_root("mission-001")
    assert first_root != second_root
    contract.seal_mission("mission-001", second_root, "12" * 32)
    assert contract.get_mission("mission-001")["effect_count"] == 2


def test_only_principal_can_seal_or_cancel(probe_vm):
    contract = load_contract(probe_vm)
    contract.create_mission("mission-001", DIGEST, 100, 200)
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
    contract.create_mission("mission-001", DIGEST, 100, 200)
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
    contract.create_mission("mission-001", DIGEST, 100, 200)
    from gltest.direct import create_address

    with pytest.raises(Exception, match=error):
        contract.prepare_effect(
            "mission-001", effect_id, digest, create_address("beneficiary"), value, expiry
        )
    assert contract.get_mission("mission-001")["effect_count"] == 0


def test_duplicate_effect_does_not_mutate_original(probe_vm):
    contract = load_contract(probe_vm)
    contract.create_mission("mission-001", DIGEST, 100, 200)
    from gltest.direct import create_address

    beneficiary = create_address("beneficiary")
    contract.prepare_effect("mission-001", "effect-001", "cd" * 32, beneficiary, 7, 200)
    with pytest.raises(Exception, match="effect already exists"):
        contract.prepare_effect("mission-001", "effect-001", "34" * 32, beneficiary, 99, 199)
    effect = contract.get_effect("mission-001", "effect-001")
    assert effect["digest"] == "cd" * 32
    assert effect["value"] == 7
    assert contract.get_mission("mission-001")["effect_count"] == 1


def test_anyone_can_recover_after_recovery_deadline(probe_vm):
    probe_vm.warp("1970-01-01T00:00:50Z")
    contract = load_contract(probe_vm)
    contract.create_mission("mission-001", DIGEST, 100, 200)
    from gltest.direct import create_address

    contract.prepare_effect(
        "mission-001", "effect-001", "cd" * 32, create_address("beneficiary"), 7, 200
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
    contract.create_mission("mission-001", DIGEST, 100, 200)
    from gltest.direct import create_address

    contract.prepare_effect(
        "mission-001", "effect-001", "cd" * 32, create_address("beneficiary"), 7, 200
    )
    contract.seal_mission("mission-001", contract.derive_effect_root("mission-001"), "12" * 32)
    probe_vm.warp("1970-01-01T00:03:20Z")
    contract.expire_mission("mission-001")
    assert contract.get_mission("mission-001")["state"] == "ABORTED"
