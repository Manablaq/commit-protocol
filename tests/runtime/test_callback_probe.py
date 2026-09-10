"""Verify local SDK syntax and payloads; do not simulate a passing consensus."""

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def load_probe(vm):
    from gltest.direct import deploy_contract
    return deploy_contract(ROOT / "probes/finalized_callback.py", vm)


def capture(vm):
    messages = []

    def hook(_vm, request):
        payload = request.get("EmitInternalMessage") or request.get("PostMessage")
        if payload is not None:
            # The direct harness exposes the v0.6 operation; accept the
            # historical spelling only so this assertion remains diagnostic.
            messages.append(payload)
            return {"ok": None}
        return None

    vm._gl_call_hook = hook
    return messages


def test_request_emits_zero_value_finalized_self_message(probe_vm):
    contract = load_probe(probe_vm)
    messages = capture(probe_vm)
    contract.request("mission-1")
    assert len(messages) == 1
    message = messages[0]
    import genlayer as gl
    assert message["address"] == gl.message.contract_address
    assert message["on"] == "finalized"
    assert message["value"] == 0
    assert message["calldata"] in (
        {"": "apply", "args": ["mission-1"]},
        {"method": "apply", "args": ["mission-1"]},
    )
    assert contract.state() == {"pending": "mission-1", "applied": False, "applications": 0}


def test_original_sender_cannot_impersonate_internal_callback(probe_vm):
    contract = load_probe(probe_vm)
    capture(probe_vm)
    contract.request("mission-1")
    with pytest.raises(Exception, match="self message required"):
        contract.apply("mission-1")
    assert contract.state()["applications"] == 0


def test_callback_binding_and_replay(probe_vm):
    contract = load_probe(probe_vm)
    capture(probe_vm)
    contract.request("mission-1")
    import genlayer as gl
    # Explicit test impersonation verifies guards, not real finality delivery.
    probe_vm.sender = gl.message.contract_address
    with pytest.raises(Exception, match="request mismatch"):
        contract.apply("mission-2")
    contract.apply("mission-1")
    contract.apply("mission-1")
    assert contract.state()["applications"] == 1


def test_nonowner_request_rejected(probe_vm):
    contract = load_probe(probe_vm)
    from gltest.direct import create_address
    probe_vm.sender = create_address("outsider")
    with pytest.raises(Exception, match="owner required"):
        contract.request("mission-1")
    assert contract.state()["pending"] == ""
