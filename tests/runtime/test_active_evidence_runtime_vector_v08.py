import importlib.util
import json
from pathlib import Path

from spec_model.onchain import decision_nonce_v3
from spec_model.provenance import (
    active_evidence_root,
    evidence_root,
)

REPAIR_TEST_PATH = Path(
    "tests/runtime/test_repairable_evidence_failures_v08.py"
)

spec = importlib.util.spec_from_file_location(
    "_repair_runtime_helpers",
    REPAIR_TEST_PATH,
)

if spec is None or spec.loader is None:
    raise RuntimeError(
        "cannot load repair runtime helpers"
    )

helpers = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helpers)


def test_runtime_vector_matches_deterministic_model(
    probe_vm,
):
    contract = helpers.load_contract(probe_vm)

    payload_a, payload_b = (
        helpers.prepare_sealed_mission(
            contract,
            probe_vm,
        )
    )

    sealed_mission = contract.get_mission(
        helpers.MISSION_ID
    )

    sealed_root = sealed_mission[
        "evidence_root"
    ]

    evidence_a = contract.get_evidence(
        helpers.MISSION_ID,
        "evidence-a",
    )

    evidence_b = contract.get_evidence(
        helpers.MISSION_ID,
        "evidence-b",
    )

    original_records = [
        {
            "evidence_id": evidence_a[
                "evidence_id"
            ],
            "authority_id": evidence_a[
                "authority_id"
            ],
            "authority_version": evidence_a[
                "authority_version"
            ],
            "issuer_address": evidence_a[
                "issuer_address"
            ],
            "record_id": evidence_a[
                "record_id"
            ],
            "record_version": evidence_a[
                "record_version"
            ],
            "mission_id": helpers.MISSION_ID,
            "mission_version": sealed_mission[
                "version"
            ],
            "url": evidence_a["url"],
            "record_hash": evidence_a[
                "record_hash"
            ],
            "subject": evidence_a[
                "subject"
            ],
            "published_at": evidence_a[
                "published_at"
            ],
            "expires_at": evidence_a[
                "expires_at"
            ],
        },
        {
            "evidence_id": evidence_b[
                "evidence_id"
            ],
            "authority_id": evidence_b[
                "authority_id"
            ],
            "authority_version": evidence_b[
                "authority_version"
            ],
            "issuer_address": evidence_b[
                "issuer_address"
            ],
            "record_id": evidence_b[
                "record_id"
            ],
            "record_version": evidence_b[
                "record_version"
            ],
            "mission_id": helpers.MISSION_ID,
            "mission_version": sealed_mission[
                "version"
            ],
            "url": evidence_b["url"],
            "record_hash": evidence_b[
                "record_hash"
            ],
            "subject": evidence_b[
                "subject"
            ],
            "published_at": evidence_b[
                "published_at"
            ],
            "expires_at": evidence_b[
                "expires_at"
            ],
        },
    ]

    assert evidence_root(
        original_records
    ) == sealed_root

    probe_vm.mock_web(
        helpers.URL_A,
        {
            "status": 503,
            "body": b"",
        },
    )

    helpers.mock_valid_b(
        contract,
        probe_vm,
        payload_b,
    )

    contract.evaluate_mission(
        helpers.MISSION_ID
    )

    failure = contract.get_evidence_failure(
        helpers.MISSION_ID,
        "evidence-a",
    )

    assert failure["status"] == (
        "REPAIR_REQUIRED"
    )

    helpers.attest(
        contract,
        probe_vm,
        authority_id=helpers.AUTHORITY_A,
        issuer=helpers.issuer_a(),
        record_id=helpers.RECORD_A,
        record_version=helpers.VERSION_2,
        url=helpers.URL_A,
        record_hash=helpers.canonical_hash(
            payload_a
        ),
    )

    probe_vm.sender = helpers.PRINCIPAL

    contract.repair_evidence(
        helpers.MISSION_ID,
        "evidence-a",
        helpers.AUTHORITY_A,
        1,
        helpers.RECORD_A,
        helpers.VERSION_2,
    )

    repair = contract.get_evidence_repair(
        helpers.MISSION_ID,
        "evidence-a",
    )

    repairs = {
        "evidence-a": {
            "status": repair["status"],
            "authority_id": repair[
                "authority_id"
            ],
            "authority_version": repair[
                "authority_version"
            ],
            "issuer_address": repair[
                "issuer_address"
            ],
            "record_id": repair[
                "record_id"
            ],
            "record_version": repair[
                "active_record_version"
            ],
            "url": repair["url"],
            "record_hash": repair[
                "record_hash"
            ],
            "published_at": repair[
                "published_at"
            ],
            "expires_at": repair[
                "expires_at"
            ],
        }
    }

    runtime_active_root = (
        contract.derive_active_evidence_root(
            helpers.MISSION_ID
        )
    )

    model_active_root = (
        active_evidence_root(
            original_records,
            repairs,
        )
    )

    assert (
        runtime_active_root
        == model_active_root
    )

    assert (
        runtime_active_root
        != sealed_root
    )

    probe_vm.clear_mocks()

    probe_vm.mock_web(
        helpers.URL_A,
        {
            "status": 200,
            "body": json.dumps(
                helpers.valid_record(
                    contract,
                    "evidence-a",
                    helpers.AUTHORITY_A,
                    helpers.URL_A,
                    payload_a,
                )
            ),
        },
    )

    helpers.mock_valid_b(
        contract,
        probe_vm,
        payload_b,
    )

    contract.evaluate_mission(
        helpers.MISSION_ID
    )

    mission = contract.get_mission(
        helpers.MISSION_ID
    )

    assert mission["decision"] == "COMMIT"

    assert (
        mission[
            "evaluation_evidence_root"
        ]
        == runtime_active_root
    )

    model_nonce = decision_nonce_v3(
        mission_id=helpers.MISSION_ID,
        mission_version=mission["version"],
        decision=mission["decision"],
        reason_code=mission[
            "reason_code"
        ],
        effect_root=mission[
            "effect_root"
        ],
        sealed_evidence_root=mission[
            "evidence_root"
        ],
        active_evidence_root=mission[
            "evaluation_evidence_root"
        ],
    )

    assert (
        model_nonce
        == mission["decision_nonce"]
    )

    print(
        "RUNTIME_SEALED_ROOT="
        + sealed_root
    )

    print(
        "RUNTIME_ACTIVE_ROOT="
        + runtime_active_root
    )

    print(
        "RUNTIME_DECISION_NONCE="
        + mission["decision_nonce"]
    )
