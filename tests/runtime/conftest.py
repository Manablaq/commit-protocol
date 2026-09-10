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
    from gltest.direct import VMContext
    from gltest.direct import sdk_loader

    # Upstream cleanup identifies SDK imports by this directory component.
    sdk_loader.CACHE_DIR = ROOT / ".runtime-cache/gltest-direct"
    vm = VMContext()
    vm.sender = bytes.fromhex("11" * 20)
    vm.origin = bytes.fromhex("11" * 20)
    with vm.activate():
        yield vm
