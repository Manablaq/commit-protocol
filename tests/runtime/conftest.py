"""Use explicitly selected release assets, with all cache writes in the repo."""

import os
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _import_calldata_compat():
    try:
        from genlayer import calldata
    except ImportError:
        import genlayer.py.calldata as calldata
    return calldata


def _import_types_compat():
    try:
        from genlayer import types
    except ImportError:
        import genlayer.py.types as types
    return types


def _install_legacy_direct_adapters(vm, loader, sdk_loader):
    """Adapt gltest-direct's v0.3 helpers to Bradbury's documented 1jb SDK.

    The production contract remains unchanged by this test-only adapter. The
    adapter supplies message injection, storage allocation, and validator
    replay for the v0.2 package selected by the contract header.
    """
    from gltest.direct import wasi_mock

    sdk_loader.setup_sdk_paths(ROOT / "contracts/commit.py")
    wasi_mock.set_vm(vm)
    sys.modules["_genlayer_wasi"] = wasi_mock
    loader._inject_message_to_fd0(vm)
    import genlayer.gl.vm as legacy_vm
    import genlayer.py.storage as legacy_storage
    wasi_mock.import_calldata = _import_calldata_compat

    def refresh_legacy_message():
        import genlayer as legacy_package
        import genlayer.gl as legacy_gl

        address_type = _import_types_compat().Address
        u256_type = _import_types_compat().u256

        def legacy_address(value):
            if hasattr(value, "as_hex"):
                return address_type(value.as_hex)
            return address_type(value)

        message = legacy_gl.MessageType(
            contract_address=legacy_address(vm._contract_address),
            sender_address=legacy_address(vm._sender),
            origin_address=legacy_address(vm._origin),
            value=u256_type(vm._value),
            chain_id=u256_type(vm._chain_id),
        )
        legacy_gl.message = message
        # The legacy top-level package does not re-export message, but keeping
        # this alias current makes test assertions match the public `gl` view.
        legacy_package.message = message

    def direct_run_nondet(leader_fn, validator_fn, /, **kwargs):
        vm._in_nondet = True
        try:
            result = leader_fn()
        finally:
            vm._in_nondet = False
        vm._captured_validators.append((result, leader_fn, validator_fn))
        return result

    legacy_vm.run_nondet = direct_run_nondet
    legacy_vm.run_nondet_unsafe = direct_run_nondet

    def allocate_legacy(contract_cls, _vm, *args, **kwargs):
        return legacy_storage.inmem_allocate(contract_cls, *args, **kwargs)

    loader._allocate_contract = allocate_legacy

    def make_legacy_proxy(instance):
        class LegacyProxy:
            def __getattr__(self, name):
                attr = getattr(instance, name)
                if not name.startswith("_") and callable(attr):
                    def wrapped(*args, **kwargs):
                        refresh_legacy_message()
                        return attr(*args, **kwargs)

                    return wrapped
                return attr

        return LegacyProxy()

    loader._make_contract_proxy = make_legacy_proxy

    def run_validator_legacy(self, *, leader_result=None, leader_error=None, index=-1):
        if not self._captured_validators:
            raise RuntimeError("No validator captured")
        stored_result, _leader_fn, validator_fn = self._captured_validators[index]
        if leader_error is not None:
            wrapped = legacy_vm.UserError(str(leader_error))
        elif leader_result is not None:
            wrapped = legacy_vm.Return(calldata=leader_result)
        else:
            wrapped = legacy_vm.Return(calldata=stored_result)
        return validator_fn(wrapped)

    vm.run_validator = run_validator_legacy.__get__(vm, type(vm))


@pytest.fixture
def probe_vm():
    if not os.environ.get("GENVM_PREBUILT_DIR"):
        pytest.fail("Set GENVM_PREBUILT_DIR to the verified extracted release tree")
    from gltest.direct import VMContext
    from gltest.direct import loader
    from gltest.direct import sdk_loader
    from gltest.direct import sdk_compat

    # Bradbury's documented 1jb runner is the legacy v0.2 package layout.
    # gltest-direct is written for the current layout and otherwise silently
    # skips message injection when `genlayer.calldata` is absent. Resolve both
    # layouts explicitly so a failed test reflects contract behavior, not a
    # harness import mismatch.
    sdk_compat.import_calldata = _import_calldata_compat
    sdk_compat.import_types = _import_types_compat
    loader.import_calldata = _import_calldata_compat
    loader.import_address = lambda: _import_types_compat().Address

    # Upstream cleanup identifies SDK imports by this directory component.
    sdk_loader.CACHE_DIR = ROOT / ".runtime-cache/gltest-direct"
    vm = VMContext()
    vm.sender = bytes.fromhex("11" * 20)
    vm.origin = bytes.fromhex("11" * 20)
    _install_legacy_direct_adapters(vm, loader, sdk_loader)
    with vm.activate():
        yield vm
