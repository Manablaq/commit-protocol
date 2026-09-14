"""Use explicitly selected release assets, with all cache writes in the repo."""

import os
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture
def probe_vm():
    if not os.environ.get("GENVM_PREBUILT_DIR"):
        pytest.fail("Set GENVM_PREBUILT_DIR to the verified extracted release tree")

    from gltest.direct import VMContext, sdk_loader
    from gltest.direct import loader as direct_loader
    from gltest.direct import vm as direct_vm
    from gltest.direct import wasi_mock

    # Use the exact qualified RC5 prebuilt tree. The installed Direct Runner
    # compatibility helpers target a newer SDK layout ("genlayer.calldata" /
    # "genlayer.types"). RC5 uses the proven "genlayer.py.*" layout instead.
    sdk_loader.CACHE_DIR = ROOT / ".runtime-cache/gltest-direct"

    original_import_calldata = getattr(
        direct_loader, "import_calldata", None
    )
    original_import_address = getattr(
        direct_loader, "import_address", None
    )
    original_import_lazy = getattr(
        direct_loader, "import_lazy", None
    )
    original_wasi_import_calldata = getattr(
        wasi_mock, "import_calldata", None
    )
    original_refresh = VMContext._refresh_gl_message
    original_run_validator = VMContext.run_validator
    original_patch_run_nondet = direct_loader._patch_run_nondet_for_direct_mode
    original_load_module = direct_loader._load_module
    original_allocate_contract = direct_loader._allocate_contract

    def rc5_import_calldata():
        from genlayer.py import calldata
        return calldata

    def rc5_import_address():
        from genlayer.py.types import Address
        return Address

    def rc5_import_lazy():
        from genlayer.py.types import Lazy
        return Lazy

    def rc5_patch_run_nondet_for_direct_mode():
        # Verified RC5 Direct Runner behavior: patch genlayer.gl.vm, not
        # genlayer.vm. This bypasses VM-boundary cloudpickle serialization
        # only in Direct Mode while still executing leader/validator closures.
        import genlayer.gl.vm as gl_vm
        from genlayer.py.types import Lazy

        if getattr(gl_vm, "_direct_mode_patched", False):
            return

        def direct_run_nondet(leader_fn, validator_fn, /, **kwargs):
            vm = wasi_mock.get_vm()
            if vm._check_pickling:
                direct_loader._validate_pickling(
                    leader_fn, "leader_fn"
                )
                direct_loader._validate_pickling(
                    validator_fn, "validator_fn"
                )
            vm._in_nondet = True
            try:
                result = leader_fn()
            finally:
                vm._in_nondet = False
            vm._captured_validators.append(
                (result, leader_fn, validator_fn)
            )
            return result

        def direct_run_nondet_unsafe(
            leader_fn, validator_fn, /
        ):
            vm = wasi_mock.get_vm()
            vm._in_nondet = True
            try:
                result = leader_fn()
            finally:
                vm._in_nondet = False
            vm._captured_validators.append(
                (result, leader_fn, validator_fn)
            )
            return result

        def lazy_run_nondet(
            leader_fn, validator_fn, /, **kwargs
        ):
            return Lazy(
                lambda: direct_run_nondet(
                    leader_fn,
                    validator_fn,
                    **kwargs,
                )
            )

        def lazy_run_nondet_unsafe(
            leader_fn, validator_fn, /
        ):
            return Lazy(
                lambda: direct_run_nondet_unsafe(
                    leader_fn,
                    validator_fn,
                )
            )

        direct_run_nondet.lazy = lazy_run_nondet
        direct_run_nondet_unsafe.lazy = (
            lazy_run_nondet_unsafe
        )

        gl_vm.run_nondet = direct_run_nondet
        gl_vm.run_nondet_unsafe = (
            direct_run_nondet_unsafe
        )
        gl_vm._direct_mode_patched = True
        gl_vm._direct_mode_unsafe_patched = True

    def rc5_run_validator(
        self,
        *,
        leader_result=direct_vm._sentinel,
        leader_error=None,
        index=-1,
    ):
        if not self._captured_validators:
            raise RuntimeError(
                "No validator captured. Call a contract method "
                "that uses gl.vm.run_nondet before calling "
                "run_validator()."
            )

        stored_result, leader_fn, validator_fn = (
            self._captured_validators[index]
        )

        import genlayer.gl.vm as gl_vm

        if leader_error is not None:
            wrapped = gl_vm.UserError(
                message=str(leader_error)
            )
        elif leader_result is not direct_vm._sentinel:
            wrapped = gl_vm.Return(
                calldata=leader_result
            )
        else:
            wrapped = gl_vm.Return(
                calldata=stored_result
            )

        return validator_fn(wrapped)

    if original_import_calldata is None:
        raise RuntimeError(
            "Direct Runner loader import_calldata hook missing"
        )
    if original_import_address is None:
        raise RuntimeError(
            "Direct Runner loader import_address hook missing"
        )
    if original_import_lazy is None:
        raise RuntimeError(
            "Direct Runner loader import_lazy hook missing"
        )
    if original_wasi_import_calldata is None:
        raise RuntimeError(
            "Direct Runner WASI import_calldata hook missing"
        )

    direct_loader.import_calldata = rc5_import_calldata
    direct_loader.import_address = rc5_import_address
    direct_loader.import_lazy = rc5_import_lazy
    wasi_mock.import_calldata = rc5_import_calldata
    direct_loader._patch_run_nondet_for_direct_mode = (
        rc5_patch_run_nondet_for_direct_mode
    )
    VMContext.run_validator = rc5_run_validator

    def rc5_refresh_gl_message(self):
        # RC5 caches message state in genlayer.gl. Do not trigger a fresh
        # genlayer.gl import here because it consumes fd 0 at import time.
        if "genlayer.gl" not in sys.modules:
            return

        gl = sys.modules["genlayer.gl"]
        from genlayer.py.types import Address, u256

        sender = self.sender
        if sender is not None and not isinstance(sender, Address):
            if isinstance(sender, bytes):
                sender = Address(sender)
            elif hasattr(sender, "as_bytes"):
                sender = Address(sender.as_bytes)

        origin = self.origin
        if origin is not None and not isinstance(origin, Address):
            if isinstance(origin, bytes):
                origin = Address(origin)
            elif hasattr(origin, "as_bytes"):
                origin = Address(origin.as_bytes)

        if hasattr(gl, "message_raw") and gl.message_raw is not None:
            gl.message_raw["sender_address"] = sender
            gl.message_raw["origin_address"] = origin

        if hasattr(gl, "message") and gl.message is not None:
            gl.message = gl.MessageType(
                contract_address=gl.message.contract_address,
                sender_address=sender,
                origin_address=origin,
                value=u256(self._value),
                chain_id=u256(self._chain_id),
            )

    VMContext._refresh_gl_message = rc5_refresh_gl_message

    def rc5_allocate_contract(contract_cls, vm, *args, **kwargs):
        # The installed Direct Runner's allocator first imports Root from
        # genlayer.py.storage. RC5's storage generator is present and active,
        # but that Root export path is not compatible, so the loader silently
        # falls through to contract_cls(*args, **kwargs), leaving __type_desc__
        # unset. Build directly from the RC5 storage generator instead.
        from genlayer.py.storage._internal.generate import (
            ORIGINAL_INIT_ATTR,
            _storage_build,
            Lit,
        )

        td = _storage_build(contract_cls, {})
        if isinstance(td, Lit):
            raise RuntimeError(
                "RC5 contract storage descriptor unexpectedly resolved to Lit"
            )

        root_slot = vm._storage.get_store_slot(b"\x00" * 32)
        instance = td.get(root_slot, 0)

        init_owner = getattr(td, "cls", None)
        if init_owner is None:
            init = getattr(contract_cls, "__init__", None)
        else:
            init = getattr(init_owner, "__init__", None)

        if init is not None:
            if hasattr(init, ORIGINAL_INIT_ATTR):
                init = getattr(init, ORIGINAL_INIT_ATTR)
            init(instance, *args, **kwargs)

        if not hasattr(instance, "__type_desc__"):
            raise RuntimeError(
                "RC5 storage allocation completed without __type_desc__"
            )

        return instance

    direct_loader._allocate_contract = rc5_allocate_contract

    # The loader itself owns fd 0 injection. This wrapper only verifies that
    # the RC5-compatible injector actually produced a non-empty regular-file
    # message buffer and rewinds it immediately before contract import.
    def load_module_with_message_rewind(contract_path):
        try:
            stat = os.fstat(0)
            size = stat.st_size
            os.lseek(0, 0, os.SEEK_SET)
        except OSError as exc:
            raise RuntimeError(
                "Direct Mode message fd is not a seekable injected buffer"
            ) from exc
        if size <= 0:
            raise RuntimeError(
                "Direct Mode RC5 message injection produced an empty buffer"
            )
        return original_load_module(contract_path)

    direct_loader._load_module = load_module_with_message_rewind

    vm = VMContext()
    vm.sender = bytes.fromhex("11" * 20)
    vm.origin = bytes.fromhex("11" * 20)

    try:
        with vm.activate():
            yield vm
    finally:
        direct_loader._load_module = original_load_module
        direct_loader._allocate_contract = original_allocate_contract
        direct_loader._patch_run_nondet_for_direct_mode = (
            original_patch_run_nondet
        )
        VMContext.run_validator = original_run_validator
        VMContext._refresh_gl_message = original_refresh
        direct_loader.import_calldata = original_import_calldata
        direct_loader.import_address = original_import_address
        direct_loader.import_lazy = original_import_lazy
        wasi_mock.import_calldata = original_wasi_import_calldata

# COMMIT v0.9 Bradbury-native Direct Runtime bridge.
#
# The pinned Direct Runner is single-contract by default. GenLayer's own
# multi-contract simulator resets the SDK Contract registry between contract
# class loads and routes CallContract through VMContext._gl_call_hook.
# This fixture applies that same boundary only for the stateless view helper.
@pytest.fixture(autouse=True)
def _commit_v09_pair_deployment(monkeypatch, probe_vm):
    import inspect
    import sys
    from pathlib import Path

    import gltest.direct as direct
    from gltest.direct import loader as direct_loader

    real_deploy = direct.deploy_contract
    sig = inspect.signature(real_deploy)
    args_param = sig.parameters.get("args")

    if (
        args_param is None
        or args_param.kind is not inspect.Parameter.VAR_POSITIONAL
    ):
        pytest.fail(
            "Pinned Direct Runner deploy_contract no longer exposes positional "
            "*args constructor parameters: " + str(sig)
        )

    coordinator_path = (ROOT / "contracts/commit.py").resolve()
    helper_path = (ROOT / "contracts/commit_helper.py").resolve()
    original_hook = getattr(probe_vm, "_gl_call_hook", None)
    deployed_pair = {"done": False}

    def _address_bytes(value):
        if isinstance(value, bytes):
            raw = value
        elif isinstance(value, bytearray):
            raw = bytes(value)
        elif isinstance(value, str):
            if not value.startswith("0x") or len(value) != 42:
                raise ValueError("non-canonical address string")
            raw = bytes.fromhex(value[2:])
        else:
            raw = getattr(value, "as_bytes", None)
            if callable(raw):
                raw = raw()
            if isinstance(raw, bytearray):
                raw = bytes(raw)

        if not isinstance(raw, bytes) or len(raw) != 20:
            raise ValueError(
                "address did not normalize to exactly 20 bytes"
            )
        return raw

    def _reset_live_contract_registry():
        gl_mod = sys.modules.get("genlayer.gl")
        if gl_mod is None:
            return "NOT_LOADED"

        contract_base = getattr(gl_mod, "Contract", None)
        if contract_base is None:
            pytest.fail("genlayer.gl.Contract is missing")

        init_subclass = getattr(
            contract_base,
            "__init_subclass__",
            None,
        )
        fn = getattr(init_subclass, "__func__", init_subclass)
        globals_dict = getattr(fn, "__globals__", None)

        if (
            not isinstance(globals_dict, dict)
            or "__known_contract__" not in globals_dict
        ):
            pytest.fail(
                "Could not locate the live GenLayer Contract registry "
                "through Contract.__init_subclass__"
            )

        globals_dict["__known_contract__"] = None

        if globals_dict["__known_contract__"] is not None:
            pytest.fail("GenLayer Contract registry reset did not stick")

        return "RESET"

    def _chain_hook(previous, vm, request):
        if previous is None:
            return None
        return previous(vm, request)

    def paired_deploy(contract_path, vm, *args, **kwargs):
        path = Path(contract_path).resolve()

        if path != coordinator_path:
            return real_deploy(contract_path, vm, *args, **kwargs)

        if vm is not probe_vm:
            pytest.fail(
                "COMMIT v0.9 coordinator deployment used an unexpected VM"
            )

        if deployed_pair["done"]:
            pytest.fail(
                "COMMIT v0.9 test attempted a second coordinator deployment "
                "inside one Direct Runtime test"
            )

        if args or kwargs:
            pytest.fail(
                "COMMIT v0.9 wrapper received unexpected constructor "
                "arguments from a legacy test"
            )

        # Clear any live Contract registry residue before loading the helper.
        _reset_live_contract_registry()

        helper = real_deploy(helper_path, vm)

        helper_addr_bytes = _address_bytes(vm._contract_address)
        Address = direct_loader.import_address()
        helper_address = Address(helper_addr_bytes)

        proxy_address = getattr(helper, "address", None)
        if (
            proxy_address is not None
            and _address_bytes(proxy_address) != helper_addr_bytes
        ):
            pytest.fail(
                "Helper proxy address disagrees with VM contract address"
            )

        status = _reset_live_contract_registry()
        if status != "RESET":
            pytest.fail(
                "Helper loaded but live Contract registry was unavailable "
                "for the coordinator reset"
            )

        # deploy_contract takes constructor values as positional *args.
        coordinator = real_deploy(
            coordinator_path,
            vm,
            helper_address,
        )

        calldata = direct_loader.import_calldata()

        def helper_call_hook(active_vm, request):
            if isinstance(request, dict) and "CallContract" in request:
                data = request["CallContract"]
                target = data.get("address")

                try:
                    target_bytes = _address_bytes(target)
                except (TypeError, ValueError):
                    target_bytes = None

                if target_bytes == helper_addr_bytes:
                    if getattr(active_vm, "_in_nondet", False):
                        raise RuntimeError(
                            "v0.9 helper cross-contract call reached hook "
                            "inside nondeterministic execution"
                        )

                    calldata_obj = data.get("calldata", {})
                    if not isinstance(calldata_obj, dict):
                        return bytes([1]) + b"invalid helper calldata object"

                    method_name = calldata_obj.get("method")
                    call_args = calldata_obj.get("args", [])
                    call_kwargs = calldata_obj.get("kwargs", {})

                    if (
                        not isinstance(method_name, str)
                        or not method_name
                        or method_name.startswith("_")
                    ):
                        return bytes([1]) + b"invalid helper method"

                    if not isinstance(call_args, list):
                        return bytes([1]) + b"invalid helper args"

                    if not isinstance(call_kwargs, dict):
                        return bytes([1]) + b"invalid helper kwargs"

                    method = getattr(helper, method_name, None)
                    if method is None or not callable(method):
                        return bytes([1]) + b"helper method not found"

                    try:
                        result = method(*call_args, **call_kwargs)
                        encoded = calldata.encode(result)
                    except Exception as exc:
                        return bytes([1]) + str(exc).encode(
                            "utf-8",
                            errors="replace",
                        )

                    # Match GenLayer's multi-contract bridge convention:
                    # ResultCode.RETURN (0) followed by calldata-encoded result.
                    return bytes([0]) + encoded

            return _chain_hook(original_hook, active_vm, request)

        vm._gl_call_hook = helper_call_hook
        deployed_pair["done"] = True
        return coordinator

    monkeypatch.setattr(direct, "deploy_contract", paired_deploy)

    try:
        yield
    finally:
        probe_vm._gl_call_hook = original_hook
