import ast
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "fee-profiles/commit-v08-policy.json"
CONTRACT_PATH = ROOT / "contracts/commit.py"

CONTRACT_SHA = (
    "1872dd0cbf92cc7edfffc4b4ab30f898584cbbf251f9ac32a1553b8b98f54b73"
)

RUNTIME_ARCHIVE_SHA = (
    "bd30580f911338d5533460eca8ed714dec371de5803c04e41dbb96430aea7b6e"
)


def load_policy():
    return json.loads(POLICY_PATH.read_text())


def message_methods_from_contract():
    source = CONTRACT_PATH.read_text()
    tree = ast.parse(source)

    methods = set()

    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef):
            continue

        for child in ast.walk(node):
            if not isinstance(child, ast.Call):
                continue

            func = child.func

            if not isinstance(func, ast.Attribute):
                continue

            if func.attr in {
                "emit",
                "emit_transfer",
            }:
                methods.add(node.name)

    return methods


def test_fee_policy_identity_is_exact():
    policy = load_policy()

    assert policy["schema"] == "commit-fee-profile-policy-v1"
    assert policy["protocol"] == "commit"
    assert policy["candidate"] == "v0.8-reviewer-hard-gates"

    assert (
        policy["contract"]["path"]
        == "contracts/commit.py"
    )

    assert (
        policy["contract"]["sha256"]
        == CONTRACT_SHA
    )

    assert (
        policy["runtime"]["version"]
        == "v0.6.0-rc5"
    )

    assert (
        policy["runtime"]["archive_sha256"]
        == RUNTIME_ARCHIVE_SHA
    )


def test_fee_policy_does_not_fabricate_network_measurements():
    policy = load_policy()

    measurement = policy["measurement"]

    assert (
        measurement["status"]
        == "TARGET_NETWORK_REQUIRED"
    )

    assert (
        measurement["numeric_fee_values_committed"]
        is False
    )

    assert (
        measurement["local_direct_mode_is_fee_evidence"]
        is False
    )

    assert (
        measurement["required_estimator"]
        == "estimateTransactionFeesForWrite"
    )

    assert measurement["required_submission_fields"] == [
        "distribution",
        "messageAllocations",
        "feeValue",
    ]


def test_fee_policy_covers_exact_message_producing_methods():
    policy = load_policy()

    paths = policy["message_paths"]

    assert {
        item["method"]
        for item in paths
    } == {
        "evaluate_mission",
        "claim_mission",
    }

    assert message_methods_from_contract() == {
        "evaluate_mission",
        "claim_mission",
    }

    by_method = {
        item["method"]: item
        for item in paths
    }

    assert (
        by_method["evaluate_mission"]["message_kind"]
        == "FINALIZED_INTERNAL_CALLBACK"
    )

    assert (
        by_method["evaluate_mission"]["child_method"]
        == "apply_decision"
    )

    assert (
        by_method["claim_mission"]["message_kind"]
        == "FINALIZED_EXTERNAL_GEN_TRANSFER"
    )

    assert (
        by_method["claim_mission"]["value_source"]
        == "EXACT_CONSUMED_MISSION_ENTITLEMENT"
    )


def test_fee_policy_keeps_protocol_fees_out_of_mission_principal():
    policy = load_policy()

    accounting = policy["accounting"]

    assert (
        accounting["mission_principal_pays_protocol_fees"]
        is False
    )

    assert (
        accounting["mission_budget_is_purchase_principal"]
        is True
    )

    assert (
        accounting["protocol_fee_measurement_is_separate"]
        is True
    )

    assert (
        accounting["contract_fee_reserve_enabled"]
        is False
    )


def test_fee_policy_requires_reproducible_live_evidence():
    policy = load_policy()

    evidence = policy["required_live_measurement_record"]

    assert evidence == [
        "network",
        "chain_id",
        "contract_address",
        "contract_source_sha256",
        "runtime_version",
        "runtime_archive_sha256",
        "method",
        "arguments_digest",
        "distribution",
        "messageAllocations",
        "feeValue",
        "transaction_id",
        "consensus_status",
        "txExecutionResultName",
        "post_state_verification",
        "measured_at",
    ]

    invalidation = set(
        policy["profile_invalidation_conditions"]
    )

    assert invalidation == {
        "contract_address_changed",
        "contract_source_changed",
        "method_changed",
        "arguments_changed",
        "message_shape_changed",
        "network_changed",
        "network_fee_policy_changed",
    }

    assert (
        policy["successful_execution_requirement"]
        == "FINISHED_WITH_RETURN"
    )
