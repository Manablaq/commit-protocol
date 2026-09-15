from pathlib import Path
import importlib.util

import pytest


HELPERS_PATH = Path(__file__).with_name(
    "test_commit_skeleton.py"
)

SPEC = importlib.util.spec_from_file_location(
    "_commit_finality_helpers",
    HELPERS_PATH,
)

if SPEC is None or SPEC.loader is None:
    raise RuntimeError(
        "unable to load COMMIT runtime helpers"
    )

helpers = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(helpers)

MISSION_ID = "mission-001"


def _queue(probe_vm):
    return probe_vm._commit_finalized_messages


def _beneficiaries():
    from gltest.direct import create_address

    return (
        create_address("beneficiary"),
        create_address(helpers.REFUND_LABEL),
    )


def _assert_no_unknown_emit_trace(probe_vm):
    assert not any(
        "EmitInternalMessage" in trace
        and "Unknown gl_call request type" in trace
        for trace in probe_vm._traces
    )


def test_commit_allocates_only_after_validator_approval_and_finality(
    probe_vm,
):
    contract = helpers.load_contract(probe_vm)

    helpers.seal_evaluable_mission(
        contract,
        probe_vm,
        True,
        True,
    )

    contract.evaluate_mission(MISSION_ID)

    pending = contract.get_mission(MISSION_ID)

    assert pending["state"] == "DECISION_PENDING"
    assert pending["decision"] == "COMMIT"
    assert pending["allocation_applied"] is False

    queue = _queue(probe_vm)
    assert len(queue) == 1

    message = queue[0]

    assert message["method"] == "apply_decision"
    assert message["on"] == "finalized"
    assert message["value"] == 0
    assert message["args"] == [
        MISSION_ID,
        pending["decision_nonce"],
    ]
    assert message["validator_checked"] is False
    assert message["validator_approved"] is False

    beneficiary, refund = _beneficiaries()

    assert contract.get_claimable(beneficiary) == 0
    assert contract.get_claimable(refund) == 0

    with pytest.raises(
        RuntimeError,
        match="validator verification",
    ):
        probe_vm._commit_finalize_next_internal_message()

    still_pending = contract.get_mission(MISSION_ID)

    assert still_pending["state"] == "DECISION_PENDING"
    assert still_pending["allocation_applied"] is False
    assert len(queue) == 1

    assert (
        probe_vm._commit_validate_next_finalized_message()
        is True
    )

    validated = contract.get_mission(MISSION_ID)

    assert validated["state"] == "DECISION_PENDING"
    assert validated["allocation_applied"] is False
    assert contract.get_claimable(beneficiary) == 0
    assert contract.get_claimable(refund) == 0
    assert len(queue) == 1

    probe_vm._commit_finalize_next_internal_message()

    committed = contract.get_mission(MISSION_ID)

    assert committed["state"] == "COMMITTED"
    assert committed["decision"] == "COMMIT"
    assert committed["allocation_applied"] is True

    assert contract.get_claimable(beneficiary) == 7
    assert contract.get_claimable(refund) == 3
    assert queue == []

    _assert_no_unknown_emit_trace(probe_vm)


def test_abort_refunds_only_after_validator_approval_and_finality(
    probe_vm,
):
    contract = helpers.load_contract(probe_vm)

    helpers.seal_evaluable_mission(
        contract,
        probe_vm,
        True,
        False,
    )

    contract.evaluate_mission(MISSION_ID)

    pending = contract.get_mission(MISSION_ID)

    assert pending["state"] == "DECISION_PENDING"
    assert pending["decision"] == "ABORT"
    assert pending["allocation_applied"] is False

    queue = _queue(probe_vm)
    assert len(queue) == 1

    message = queue[0]

    assert message["method"] == "apply_decision"
    assert message["on"] == "finalized"
    assert message["value"] == 0
    assert message["args"] == [
        MISSION_ID,
        pending["decision_nonce"],
    ]

    beneficiary, refund = _beneficiaries()

    assert contract.get_claimable(beneficiary) == 0
    assert contract.get_claimable(refund) == 0

    assert (
        probe_vm._commit_validate_next_finalized_message()
        is True
    )

    validated = contract.get_mission(MISSION_ID)

    assert validated["state"] == "DECISION_PENDING"
    assert validated["allocation_applied"] is False
    assert contract.get_claimable(beneficiary) == 0
    assert contract.get_claimable(refund) == 0
    assert len(queue) == 1

    probe_vm._commit_finalize_next_internal_message()

    aborted = contract.get_mission(MISSION_ID)

    assert aborted["state"] == "ABORTED"
    assert aborted["decision"] == "ABORT"
    assert aborted["allocation_applied"] is True

    assert contract.get_claimable(beneficiary) == 0
    assert contract.get_claimable(refund) == 10
    assert queue == []

    _assert_no_unknown_emit_trace(probe_vm)
