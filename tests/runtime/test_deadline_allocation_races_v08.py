"""Adversarial allocation/deadline race proofs for the v0.8 reviewer gates.

These tests intentionally reuse the already-certified Direct Mode mission
construction helpers. They add no new protocol behavior: they prove that only
one terminal economic allocation can win when finality and timeout recovery
race.
"""

from pathlib import Path
import importlib.util

import pytest


_HELPERS_PATH = Path(__file__).with_name(
    "test_commit_skeleton.py"
)

_SPEC = importlib.util.spec_from_file_location(
    "commit_runtime_race_helpers",
    _HELPERS_PATH,
)

if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError(
        "unable to load committed runtime helpers"
    )

helpers = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(helpers)


MISSION_ID = "mission-001"
RECOVERY_WARP = "2065-01-24T05:21:41Z"


def _addresses():
    from gltest.direct import create_address

    return (
        create_address("beneficiary"),
        create_address(helpers.REFUND_LABEL),
        create_address("recovery-keeper"),
    )


def _assert_exact_commit_allocation(contract):
    beneficiary, refund, _keeper = _addresses()

    assert contract.get_mission_claimable(
        MISSION_ID,
        beneficiary,
    ) == 7

    assert contract.get_mission_claimable(
        MISSION_ID,
        refund,
    ) == 3

    assert contract.get_claimable(
        beneficiary,
    ) == 7

    assert contract.get_claimable(
        refund,
    ) == 3

    assert (
        contract.get_mission_claimable(
            MISSION_ID,
            beneficiary,
        )
        + contract.get_mission_claimable(
            MISSION_ID,
            refund,
        )
        == 10
    )


def _assert_exact_abort_allocation(contract):
    beneficiary, refund, _keeper = _addresses()

    assert contract.get_mission_claimable(
        MISSION_ID,
        beneficiary,
    ) == 0

    assert contract.get_mission_claimable(
        MISSION_ID,
        refund,
    ) == 10

    assert contract.get_claimable(
        beneficiary,
    ) == 0

    assert contract.get_claimable(
        refund,
    ) == 10

    assert (
        contract.get_mission_claimable(
            MISSION_ID,
            beneficiary,
        )
        + contract.get_mission_claimable(
            MISSION_ID,
            refund,
        )
        == 10
    )


def test_recovery_winner_blocks_exact_stale_commit_nonce_without_double_allocation(
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

    pending = contract.get_mission(
        MISSION_ID
    )

    assert pending["state"] == "DECISION_PENDING"
    assert pending["decision"] == "COMMIT"
    assert pending["allocation_applied"] is False

    original_nonce = pending["decision_nonce"]

    _beneficiary, _refund, keeper = _addresses()

    probe_vm.warp(RECOVERY_WARP)
    probe_vm.sender = keeper

    contract.expire_mission(MISSION_ID)

    recovered = contract.get_mission(
        MISSION_ID
    )

    assert recovered["state"] == "ABORTED"
    assert recovered["decision"] == "ABORT"
    assert (
        recovered["reason_code"]
        == "recovery_deadline_expired"
    )
    assert recovered["allocation_applied"] is True

    _assert_exact_abort_allocation(contract)

    import genlayer.gl as gl

    probe_vm.sender = gl.message.contract_address

    contract.apply_decision(
        MISSION_ID,
        original_nonce,
    )

    contract.apply_decision(
        MISSION_ID,
        original_nonce,
    )

    after_late_callbacks = contract.get_mission(
        MISSION_ID
    )

    assert after_late_callbacks["state"] == "ABORTED"
    assert after_late_callbacks["decision"] == "ABORT"
    assert (
        after_late_callbacks["reason_code"]
        == "recovery_deadline_expired"
    )

    _assert_exact_abort_allocation(contract)


def test_finalized_commit_winner_blocks_late_recovery_without_reallocation(
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

    pending = contract.get_mission(
        MISSION_ID
    )

    import genlayer.gl as gl

    probe_vm.sender = gl.message.contract_address

    contract.apply_decision(
        MISSION_ID,
        pending["decision_nonce"],
    )

    committed = contract.get_mission(
        MISSION_ID
    )

    assert committed["state"] == "COMMITTED"
    assert committed["decision"] == "COMMIT"
    assert committed["allocation_applied"] is True

    _assert_exact_commit_allocation(contract)

    _beneficiary, _refund, keeper = _addresses()

    probe_vm.warp(RECOVERY_WARP)
    probe_vm.sender = keeper

    with pytest.raises(
        Exception,
        match="already terminal",
    ):
        contract.expire_mission(MISSION_ID)

    after_recovery_attempt = contract.get_mission(
        MISSION_ID
    )

    assert after_recovery_attempt["state"] == "COMMITTED"
    assert after_recovery_attempt["decision"] == "COMMIT"
    assert after_recovery_attempt["allocation_applied"] is True

    _assert_exact_commit_allocation(contract)


def test_finalized_abort_winner_blocks_late_recovery_and_refunds_exactly_once(
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

    pending = contract.get_mission(
        MISSION_ID
    )

    assert pending["state"] == "DECISION_PENDING"
    assert pending["decision"] == "ABORT"
    assert pending["allocation_applied"] is False

    import genlayer.gl as gl

    probe_vm.sender = gl.message.contract_address

    contract.apply_decision(
        MISSION_ID,
        pending["decision_nonce"],
    )

    contract.apply_decision(
        MISSION_ID,
        pending["decision_nonce"],
    )

    aborted = contract.get_mission(
        MISSION_ID
    )

    assert aborted["state"] == "ABORTED"
    assert aborted["decision"] == "ABORT"
    assert (
        aborted["reason_code"]
        == "policy_or_source_ineligible"
    )
    assert aborted["allocation_applied"] is True

    _assert_exact_abort_allocation(contract)

    _beneficiary, _refund, keeper = _addresses()

    probe_vm.warp(RECOVERY_WARP)
    probe_vm.sender = keeper

    with pytest.raises(
        Exception,
        match="already terminal",
    ):
        contract.expire_mission(MISSION_ID)

    _assert_exact_abort_allocation(contract)


def test_timeout_allocation_is_terminal_even_after_multiple_callback_attempts(
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

    pending = contract.get_mission(
        MISSION_ID
    )

    original_nonce = pending["decision_nonce"]

    _beneficiary, _refund, keeper = _addresses()

    probe_vm.warp(RECOVERY_WARP)
    probe_vm.sender = keeper

    contract.expire_mission(MISSION_ID)

    _assert_exact_abort_allocation(contract)

    import genlayer.gl as gl

    probe_vm.sender = gl.message.contract_address

    for nonce in (
        original_nonce,
        "00" * 32,
        original_nonce,
    ):
        contract.apply_decision(
            MISSION_ID,
            nonce,
        )

    final = contract.get_mission(
        MISSION_ID
    )

    assert final["state"] == "ABORTED"
    assert final["decision"] == "ABORT"
    assert final["allocation_applied"] is True

    _assert_exact_abort_allocation(contract)
