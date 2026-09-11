"""Reviewer hard-gate tests for authenticated, versioned evidence.

These tests certify the authenticated-evidence surface implemented by the
current COMMIT reviewer-hard-gates candidate.

Authority authentication does not assume an unsupported in-GenVM signature
library. The approved issuer is a GenLayer account address and proves control
by submitting the attestation transaction itself; the contract authenticates
that transaction with gl.message.sender_address.

The evidence attestation is immutable and binds:
- authority identity + authority version
- stable evidence record id + record version
- mission id + mission version
- immutable URL + exact content/payload digest
- publication timestamp + expiry

The mission principal may attach only an existing authenticated attestation.
"""

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]

DIGEST = (
    "983307fac383ac4a92be6c0c361ea8f3c9d9efa20ad5e6e8bc8dee932f2a6103"
)

OBJECTIVE = "Procure a verified sensor package"

PRINCIPAL = bytes.fromhex("11" * 20)

MISSION_ID = "mission-reviewer-gates-001"

PREPARE = 3_000_000_000
RECOVERY = 3_000_000_100

# The Direct harness transaction clock defaults well before these future
# mission deadlines. Tests that need an exact clock set probe_vm.datetime.
PUBLISHED = 2_000_000_000
EXPIRES = RECOVERY

AUTHORITY_A = "publisher-a"
AUTHORITY_B = "publisher-b"

AUTHORITY_VERSION = 1
RECORD_VERSION = 1

RECORD_A = "sensor-proof-a-001"
RECORD_B = "sensor-proof-b-001"

URL_A = "https://publisher-a.example/records/sensor-proof-a-001/v1"
URL_B = "https://publisher-b.example/records/sensor-proof-b-001/v1"

HASH_A = "12" * 32
HASH_B = "34" * 32


def load_contract(vm):
    from gltest.direct import deploy_contract

    return deploy_contract(ROOT / "contracts/commit.py", vm)


def addr(label):
    from gltest.direct import create_address

    return create_address(label)


def issuer_a():
    return addr("authority-issuer-a")


def issuer_b():
    return addr("authority-issuer-b")


def refund():
    return addr("refund-beneficiary")


def register_authenticated_authorities(contract, probe_vm):
    """Desired v0.8 authority API.

    register_authority must bind the authority's network origin to one exact
    issuer/attestor address and immutable authority version.
    """

    probe_vm.sender = PRINCIPAL

    contract.register_authority(
        AUTHORITY_A,
        "publisher-a.example",
        "/records",
        issuer_a(),
        AUTHORITY_VERSION,
    )

    contract.register_authority(
        AUTHORITY_B,
        "publisher-b.example",
        "/records",
        issuer_b(),
        AUTHORITY_VERSION,
    )


def create_mission(contract, probe_vm):
    probe_vm.sender = PRINCIPAL

    contract.create_mission(
        MISSION_ID,
        OBJECTIVE,
        DIGEST,
        10,
        refund(),
        PREPARE,
        RECOVERY,
    )


def attest_a(contract, probe_vm, **overrides):
    """Submit authority A's desired immutable on-chain evidence attestation."""

    values = {
        "authority_id": AUTHORITY_A,
        "authority_version": AUTHORITY_VERSION,
        "record_id": RECORD_A,
        "record_version": RECORD_VERSION,
        "mission_id": MISSION_ID,
        "mission_version": 1,
        "url": URL_A,
        "record_hash": HASH_A,
        "published_at": PUBLISHED,
        "expires_at": EXPIRES,
    }
    values.update(overrides)

    probe_vm.sender = issuer_a()

    contract.attest_evidence(
        values["authority_id"],
        values["authority_version"],
        values["record_id"],
        values["record_version"],
        values["mission_id"],
        values["mission_version"],
        values["url"],
        values["record_hash"],
        values["published_at"],
        values["expires_at"],
    )


def test_authority_registry_binds_authenticated_issuer_address_and_version(
    probe_vm,
):
    contract = load_contract(probe_vm)

    register_authenticated_authorities(contract, probe_vm)

    authority = contract.get_authority(AUTHORITY_A)

    assert authority["authority_id"] == AUTHORITY_A
    assert authority["host"] == "publisher-a.example"
    assert authority["path_prefix"] == "/records"

    # Reviewer hard gate: authority identity must be more than URL provenance.
    assert authority["issuer_address"] == issuer_a()
    assert authority["authority_version"] == AUTHORITY_VERSION


def test_authority_registration_rejects_zero_issuer_address(probe_vm):
    contract = load_contract(probe_vm)

    # The pinned Direct runtime requires an actual GenLayer Address object.
    # Derive the exact runtime Address class from a normalized address already
    # returned by create_address(), then construct the canonical zero address.
    zero_issuer = type(issuer_a())(bytes(20))

    probe_vm.sender = PRINCIPAL

    with pytest.raises(Exception, match="issuer"):
        contract.register_authority(
            AUTHORITY_A,
            "publisher-a.example",
            "/records",
            zero_issuer,
            AUTHORITY_VERSION,
        )


def test_only_registered_issuer_address_can_attest_for_authority(probe_vm):
    contract = load_contract(probe_vm)

    register_authenticated_authorities(contract, probe_vm)
    create_mission(contract, probe_vm)

    # An arbitrary mission participant must not be able to impersonate the
    # approved evidence publisher merely by knowing its authority_id.
    probe_vm.sender = addr("attacker")

    with pytest.raises(Exception, match="issuer"):
        contract.attest_evidence(
            AUTHORITY_A,
            AUTHORITY_VERSION,
            RECORD_A,
            RECORD_VERSION,
            MISSION_ID,
            1,
            URL_A,
            HASH_A,
            PUBLISHED,
            EXPIRES,
        )


def test_authenticated_attestation_binds_full_versioned_record(probe_vm):
    contract = load_contract(probe_vm)

    register_authenticated_authorities(contract, probe_vm)
    create_mission(contract, probe_vm)
    attest_a(contract, probe_vm)

    attestation = contract.get_evidence_attestation(
        AUTHORITY_A,
        RECORD_A,
        RECORD_VERSION,
    )

    assert attestation == {
        "authority_id": AUTHORITY_A,
        "authority_version": AUTHORITY_VERSION,
        "issuer_address": issuer_a(),
        "record_id": RECORD_A,
        "record_version": RECORD_VERSION,
        "mission_id": MISSION_ID,
        "mission_version": 1,
        "url": URL_A,
        "record_hash": HASH_A,
        "published_at": PUBLISHED,
        "expires_at": EXPIRES,
    }


def test_attestation_rejects_wrong_mission_version(probe_vm):
    contract = load_contract(probe_vm)

    register_authenticated_authorities(contract, probe_vm)
    create_mission(contract, probe_vm)

    with pytest.raises(Exception, match="mission version"):
        attest_a(contract, probe_vm, mission_version=2)


def test_attestation_record_version_is_positive_and_immutable(probe_vm):
    contract = load_contract(probe_vm)

    register_authenticated_authorities(contract, probe_vm)
    create_mission(contract, probe_vm)

    with pytest.raises(Exception, match="record version"):
        attest_a(contract, probe_vm, record_version=0)

    attest_a(contract, probe_vm)

    # Same authority + record_id + version is an immutable identity. Reusing
    # it with different bytes must not rewrite history.
    with pytest.raises(Exception, match="attestation already exists"):
        attest_a(contract, probe_vm, record_hash="56" * 32)


def test_attestation_rejects_pre_mission_stale_publication(probe_vm):
    contract = load_contract(probe_vm)

    register_authenticated_authorities(contract, probe_vm)

    # Pin mission creation at a deterministic transaction timestamp so the
    # freshness rule is exact and has no arbitrary "N days" assumption.
    probe_vm.warp("2033-05-18T03:33:20Z")  # unix 2_000_000_000
    create_mission(contract, probe_vm)

    mission = contract.get_mission(MISSION_ID)

    assert mission["created_at"] == 2_000_000_000

    # A record published before this mission existed is stale for this
    # mission/version even if its HTTP URL and hash are otherwise valid.
    with pytest.raises(Exception, match="published"):
        attest_a(
            contract,
            probe_vm,
            published_at=1_999_999_999,
        )


def test_attestation_must_remain_valid_through_recovery_deadline(probe_vm):
    contract = load_contract(probe_vm)

    register_authenticated_authorities(contract, probe_vm)
    create_mission(contract, probe_vm)

    with pytest.raises(Exception, match="expiry"):
        attest_a(
            contract,
            probe_vm,
            expires_at=RECOVERY - 1,
        )


def test_mission_evidence_requires_authenticated_attestation(probe_vm):
    contract = load_contract(probe_vm)

    register_authenticated_authorities(contract, probe_vm)
    create_mission(contract, probe_vm)

    # The principal cannot create "publisher evidence" from URL/hash metadata
    # alone. The exact authority attestation must already exist.
    probe_vm.sender = PRINCIPAL

    with pytest.raises(Exception, match="attestation"):
        contract.register_evidence(
            MISSION_ID,
            "evidence-a",
            AUTHORITY_A,
            AUTHORITY_VERSION,
            RECORD_A,
            RECORD_VERSION,
        )

    attest_a(contract, probe_vm)

    probe_vm.sender = PRINCIPAL
    contract.register_evidence(
        MISSION_ID,
        "evidence-a",
        AUTHORITY_A,
        AUTHORITY_VERSION,
        RECORD_A,
        RECORD_VERSION,
    )

    evidence = contract.get_evidence(MISSION_ID, "evidence-a")

    assert evidence["authority_id"] == AUTHORITY_A
    assert evidence["authority_version"] == AUTHORITY_VERSION
    assert evidence["issuer_address"] == issuer_a()
    assert evidence["record_id"] == RECORD_A
    assert evidence["record_version"] == RECORD_VERSION
    assert evidence["mission_version"] == 1
    assert evidence["published_at"] == PUBLISHED
    assert evidence["expires_at"] == EXPIRES
    assert evidence["url"] == URL_A
    assert evidence["record_hash"] == HASH_A


def test_record_version_cannot_be_replayed_into_another_mission(probe_vm):
    contract = load_contract(probe_vm)

    register_authenticated_authorities(contract, probe_vm)
    create_mission(contract, probe_vm)
    attest_a(contract, probe_vm)

    probe_vm.sender = PRINCIPAL

    contract.create_mission(
        "mission-reviewer-gates-002",
        OBJECTIVE,
        DIGEST,
        10,
        refund(),
        PREPARE,
        RECOVERY,
    )

    # An attestation explicitly issued for mission/version 001/1 cannot be
    # attached to mission 002 merely because record_id/version/hash match.
    with pytest.raises(Exception, match="mission"):
        contract.register_evidence(
            "mission-reviewer-gates-002",
            "replayed-evidence",
            AUTHORITY_A,
            AUTHORITY_VERSION,
            RECORD_A,
            RECORD_VERSION,
        )


def test_corroboration_requires_distinct_authenticated_issuers(probe_vm):
    contract = load_contract(probe_vm)

    probe_vm.sender = PRINCIPAL

    # Distinct authority IDs and distinct origins are not enough if both are
    # controlled by the same authenticated issuer key/address.
    shared_issuer = issuer_a()

    contract.register_authority(
        AUTHORITY_A,
        "publisher-a.example",
        "/records",
        shared_issuer,
        AUTHORITY_VERSION,
    )
    contract.register_authority(
        AUTHORITY_B,
        "publisher-b.example",
        "/records",
        shared_issuer,
        AUTHORITY_VERSION,
    )

    create_mission(contract, probe_vm)

    # We do not need to reach settlement. The authority registry itself must
    # expose that these are not independent corroborators, and sealing must
    # eventually reject this configuration.
    assert (
        contract.get_authority(AUTHORITY_A)["issuer_address"]
        == contract.get_authority(AUTHORITY_B)["issuer_address"]
    )

    assert contract.authorities_are_independent(
        AUTHORITY_A,
        AUTHORITY_B,
    ) is False
