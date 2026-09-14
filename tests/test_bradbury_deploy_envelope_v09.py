import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COORD = ROOT / "contracts/commit.py"
HELPER = ROOT / "contracts/commit_helper.py"
POLICY = ROOT / "fee-profiles/commit-v08-policy.json"

COORD_SHA = "e88d1d78ee8f2d373124bbfbc3f0c8d946385a3250fc028f5956fd74762f8c69"
HELPER_SHA = "0120b74e0988f2444c3cc824bd40633c472348da9e1d3fd851c4d7380ffbe632"
MEASURED_SYNTHETIC_BOUNDARY = 20185

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def test_v09_sources_are_bound_and_under_measured_boundary():
    assert sha(COORD) == COORD_SHA
    assert sha(HELPER) == HELPER_SHA
    assert len(COORD.read_bytes()) <= MEASURED_SYNTHETIC_BOUNDARY
    assert len(HELPER.read_bytes()) <= MEASURED_SYNTHETIC_BOUNDARY
    ast.parse(COORD.read_text())
    ast.parse(HELPER.read_text())

def test_v09_coordinator_has_no_duplicate_public_decorators():
    tree = ast.parse(COORD.read_text())
    cls = next(x for x in tree.body if isinstance(x, ast.ClassDef) and x.name == "CommitProtocol")
    public_count = 0
    for fn in [x for x in cls.body if isinstance(x, ast.FunctionDef)]:
        decorators = [ast.unparse(d) for d in fn.decorator_list]
        assert len(decorators) == len(set(decorators)), (fn.name, decorators)
        if any(d.startswith("gl.public.") for d in decorators):
            public_count += 1
    assert public_count == 41

def test_v09_coordinator_json_helper_is_non_recursive():
    tree = ast.parse(COORD.read_text())
    cls = next(x for x in tree.body if isinstance(x, ast.ClassDef) and x.name == "CommitProtocol")
    fn = next(x for x in cls.body if isinstance(x, ast.FunctionDef) and x.name == "g")
    calls = [x for x in ast.walk(fn) if isinstance(x, ast.Call)]
    assert any(
        isinstance(call.func, ast.Attribute)
        and isinstance(call.func.value, ast.Name)
        and call.func.value.id == "json"
        and call.func.attr == "dumps"
        for call in calls
    )
    assert not any(
        isinstance(call.func, ast.Attribute)
        and isinstance(call.func.value, ast.Name)
        and call.func.value.id == "self"
        and call.func.attr == "g"
        for call in calls
    )

def test_v09_helper_is_stateless_view_only():
    tree = ast.parse(HELPER.read_text())
    cls = next(x for x in tree.body if isinstance(x, ast.ClassDef) and x.name == "CommitHelper")
    assert not any(isinstance(x, ast.AnnAssign) for x in cls.body)
    for fn in [x for x in cls.body if isinstance(x, ast.FunctionDef)]:
        decorators = [ast.unparse(d) for d in fn.decorator_list]
        if decorators:
            assert decorators == ["gl.public.view"]
    source = HELPER.read_text()
    assert "gl.nondet" not in source
    assert "gl.message" not in source
    assert "gl.get_contract_at" not in source
    assert ".emit(" not in source
    assert "emit_transfer" not in source

def test_v09_fee_policy_binds_helper():
    policy = json.loads(POLICY.read_text())
    helper = policy["helper_contract"]
    assert helper["path"] == "contracts/commit_helper.py"
    assert helper["sha256"] == HELPER_SHA
    assert helper["role"] == "STATELESS_DETERMINISTIC_VIEW_HELPER"
    assert "helper_contract_changed" in policy["profile_invalidation_conditions"]
