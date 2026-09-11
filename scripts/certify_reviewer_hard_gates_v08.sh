#!/usr/bin/env bash

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

EXPECTED_RUNTIME_SHA="bd30580f911338d5533460eca8ed714dec371de5803c04e41dbb96430aea7b6e"
EXPECTED_CONTRACT_SHA="a30ad68c62b589edf68d641092a39a0fa4a3a5c19a3c2993cd68cd6f48df0d37"
EXPECTED_PROVENANCE_MODEL_SHA="46684ee7657f876a9667d0b3158315bed725d7473ac0e7692e5b2d1bf4998641"
EXPECTED_ONCHAIN_MODEL_SHA="03f26a0bd69ad6eca5d6e5aceb6dd324332a884ec6b819149aa9c5f5934117d3"
EXPECTED_LEGACY_SHA="b73386a814d39b91b381009fdf006e30876b084d4a7e67f6d87e3295fa566a1c"
EXPECTED_REPAIR_SHA="2d6952c0eda64b54f6aa687ef117fadc3ea41a9179a761384eb1f77c7a883458"
EXPECTED_PARITY_SHA="54db4ce2426e16364606c8dcbe5caada379237493a9c8356d8fd947e1b8152a8"
EXPECTED_VECTOR_SHA="abc2befc25fb3c73f44dda7d7a214af22497cd18c0bb7c0e08a09c3a6fc54e4e"
EXPECTED_RACE_SHA="d64aaf53c1c65d4d32c9e1ec0fe3ae0051fe5f50828c9fbfc2a6ae5f233730f4"
EXPECTED_FEE_POLICY_SHA="9d2e599aa2041f48abc7969d56ff9d1e819bf1ad3a895886f92e668d19661c66"
EXPECTED_FEE_POLICY_TEST_SHA="7586ab7d94201545143068565f0d5c03f7374b98fac9719359e2bd18ce9480cc"
EXPECTED_PROVENANCE_TEST_SHA="f29e50a2156806eac774516e256f3c8d069abe645f5ac103da1721d0ab1604d0"
EXPECTED_HARD_GATE_SHA="bbb04e2c004a071ac99c8ae067c265e058e7b0fdaa88b6e9e6bdb732f4baad21"
EXPECTED_README_SHA="b6c8ce4a6cb7f975220e1b98988f1c7b9182490494f8720df201636a7d7a52bd"
EXPECTED_EVIDENCE_MODEL_SHA="5a0b1d5bc23be8b2ee56f389a8d9dfa97872db1ec350c92d804764efad20a754"
EXPECTED_STATE_MACHINE_SHA="bb629ddb822b8a143b0cb68405f89aeab8e0962f8678d07a1672fe9d35012445"
EXPECTED_THREAT_MODEL_SHA="63911926c2cd32b7e26efec4ebb179c8b66cff025ecc696a91675227af928131"

: "${GENVM_PREBUILT_DIR:?Set GENVM_PREBUILT_DIR to the verified extracted v0.6.0-rc3 release tree}"
: "${GENVM_ARCHIVE:?Set GENVM_ARCHIVE to the verified v0.6.0-rc3 genvm-universal archive}"

test -d "$GENVM_PREBUILT_DIR"
test -f "$GENVM_PREBUILT_DIR/.extracted"
test -f "$GENVM_ARCHIVE"

sha256() {
  shasum -a 256 "$1" | awk '{print $1}'
}

assert_sha() {
  local label="$1"
  local file="$2"
  local expected="$3"
  local actual
  actual="$(sha256 "$file")"
  echo "$label=$actual"
  test "$actual" = "$expected"
}

ACTUAL_RUNTIME_SHA="$(sha256 "$GENVM_ARCHIVE")"
echo "RUNTIME_ARCHIVE_SHA=$ACTUAL_RUNTIME_SHA"
test "$ACTUAL_RUNTIME_SHA" = "$EXPECTED_RUNTIME_SHA"

assert_sha CONTRACT_SHA contracts/commit.py "$EXPECTED_CONTRACT_SHA"
assert_sha PROVENANCE_MODEL_SHA spec_model/provenance.py "$EXPECTED_PROVENANCE_MODEL_SHA"
assert_sha ONCHAIN_MODEL_SHA spec_model/onchain.py "$EXPECTED_ONCHAIN_MODEL_SHA"
assert_sha LEGACY_RUNTIME_TEST_SHA tests/runtime/test_commit_skeleton.py "$EXPECTED_LEGACY_SHA"
assert_sha REPAIR_RUNTIME_TEST_SHA tests/runtime/test_repairable_evidence_failures_v08.py "$EXPECTED_REPAIR_SHA"
assert_sha ACTIVE_ROOT_PARITY_TEST_SHA tests/test_active_evidence_decision_v3.py "$EXPECTED_PARITY_SHA"
assert_sha ACTIVE_ROOT_RUNTIME_VECTOR_SHA tests/runtime/test_active_evidence_runtime_vector_v08.py "$EXPECTED_VECTOR_SHA"
assert_sha DEADLINE_ALLOCATION_RACE_TEST_SHA tests/runtime/test_deadline_allocation_races_v08.py "$EXPECTED_RACE_SHA"
assert_sha FEE_POLICY_SHA fee-profiles/commit-v08-policy.json "$EXPECTED_FEE_POLICY_SHA"
assert_sha FEE_POLICY_TEST_SHA tests/test_fee_profile_policy_v08.py "$EXPECTED_FEE_POLICY_TEST_SHA"
assert_sha PROVENANCE_TEST_SHA tests/test_provenance.py "$EXPECTED_PROVENANCE_TEST_SHA"
assert_sha REVIEWER_HARD_GATE_TEST_SHA tests/runtime/test_reviewer_hard_gates_v08.py "$EXPECTED_HARD_GATE_SHA"
assert_sha README_SHA README.md "$EXPECTED_README_SHA"
assert_sha EVIDENCE_MODEL_SHA docs/EVIDENCE_MODEL.md "$EXPECTED_EVIDENCE_MODEL_SHA"
assert_sha STATE_MACHINE_SHA docs/STATE_MACHINE.md "$EXPECTED_STATE_MACHINE_SHA"
assert_sha THREAT_MODEL_SHA docs/THREAT_MODEL.md "$EXPECTED_THREAT_MODEL_SHA"

uv sync --frozen

uv run genvm-lint lint contracts/commit.py
uv run genvm-lint validate contracts/commit.py
uv run genvm-lint typecheck contracts/commit.py
uv run genvm-lint check contracts/commit.py

SCHEMA_FILE="/tmp/commit-step2-reviewer-schema.txt"
uv run genvm-lint schema contracts/commit.py >"$SCHEMA_FILE"

python3 - "$SCHEMA_FILE" <<'PY2'
from pathlib import Path
import re
import sys

text = Path(sys.argv[1]).read_text()

match = re.search(r"Methods\s*\(([0-9]+)\):", text)
if match is None:
    raise SystemExit("STOP: schema method count unavailable")

if int(match.group(1)) != 41:
    raise SystemExit("STOP: expected 41 ABI methods")

required = (
    "derive_active_evidence_root",
    "get_evidence_failure",
    "get_evidence_repair",
    "get_mission_manifest",
    "get_mission_receipt",
    "repair_evidence",
)

for name in required:
    if name not in text:
        raise SystemExit("STOP: missing ABI method " + name)

print("SCHEMA_METHOD_COUNT=41")
print("SCHEMA_REQUIRED_METHODS=PASS")
PY2

uv run python -m pytest -q tests/test_*.py

GENVM_PREBUILT_DIR="$GENVM_PREBUILT_DIR" \
uv run python -m pytest -q tests/runtime/test_reviewer_hard_gates_v08.py

GENVM_PREBUILT_DIR="$GENVM_PREBUILT_DIR" \
uv run python -m pytest -q tests/runtime/test_repairable_evidence_failures_v08.py

GENVM_PREBUILT_DIR="$GENVM_PREBUILT_DIR" \
uv run python -m pytest -q tests/runtime/test_active_evidence_runtime_vector_v08.py

GENVM_PREBUILT_DIR="$GENVM_PREBUILT_DIR" \
uv run python -m pytest -q tests/runtime/test_deadline_allocation_races_v08.py

GENVM_PREBUILT_DIR="$GENVM_PREBUILT_DIR" \
uv run python -m pytest -q tests/runtime

GENVM_PREBUILT_DIR="$GENVM_PREBUILT_DIR" \
uv run python -m pytest -q

DETERMINISTIC_COUNT="$(
  uv run python -m pytest --collect-only -q tests/test_*.py 2>/dev/null |
  grep -Eo '[0-9]+ tests? collected' |
  tail -1 |
  grep -Eo '^[0-9]+'
)"

RUNTIME_COUNT="$(
  GENVM_PREBUILT_DIR="$GENVM_PREBUILT_DIR" \
  uv run python -m pytest --collect-only -q tests/runtime 2>/dev/null |
  grep -Eo '[0-9]+ tests? collected' |
  tail -1 |
  grep -Eo '^[0-9]+'
)"

FULL_COUNT="$(
  GENVM_PREBUILT_DIR="$GENVM_PREBUILT_DIR" \
  uv run python -m pytest --collect-only -q 2>/dev/null |
  grep -Eo '[0-9]+ tests? collected' |
  tail -1 |
  grep -Eo '^[0-9]+'
)"

HARD_GATE_COUNT="$(
  GENVM_PREBUILT_DIR="$GENVM_PREBUILT_DIR" \
  uv run python -m pytest --collect-only -q tests/runtime/test_reviewer_hard_gates_v08.py 2>/dev/null |
  grep -Eo '[0-9]+ tests? collected' |
  tail -1 |
  grep -Eo '^[0-9]+'
)"

REPAIR_COUNT="$(
  GENVM_PREBUILT_DIR="$GENVM_PREBUILT_DIR" \
  uv run python -m pytest --collect-only -q tests/runtime/test_repairable_evidence_failures_v08.py 2>/dev/null |
  grep -Eo '[0-9]+ tests? collected' |
  tail -1 |
  grep -Eo '^[0-9]+'
)"

VECTOR_COUNT="$(
  GENVM_PREBUILT_DIR="$GENVM_PREBUILT_DIR" \
  uv run python -m pytest --collect-only -q tests/runtime/test_active_evidence_runtime_vector_v08.py 2>/dev/null |
  grep -Eo '[0-9]+ tests? collected' |
  tail -1 |
  grep -Eo '^[0-9]+'
)"

RACE_COUNT="$(
  GENVM_PREBUILT_DIR="$GENVM_PREBUILT_DIR" \
  uv run python -m pytest --collect-only -q tests/runtime/test_deadline_allocation_races_v08.py 2>/dev/null |
  grep -Eo '[0-9]+ tests? collected' |
  tail -1 |
  grep -Eo '^[0-9]+'
)"

echo "DETERMINISTIC_COUNT=$DETERMINISTIC_COUNT"
echo "RUNTIME_COUNT=$RUNTIME_COUNT"
echo "FULL_COUNT=$FULL_COUNT"
echo "HARD_GATE_COUNT=$HARD_GATE_COUNT"
echo "REPAIR_COUNT=$REPAIR_COUNT"
echo "VECTOR_COUNT=$VECTOR_COUNT"
echo "RACE_COUNT=$RACE_COUNT"

test "$DETERMINISTIC_COUNT" = "35"
test "$RUNTIME_COUNT" = "113"
test "$FULL_COUNT" = "148"
test "$HARD_GATE_COUNT" = "11"
test "$REPAIR_COUNT" = "18"
test "$VECTOR_COUNT" = "1"
test "$RACE_COUNT" = "4"

python3 <<'PY2'
from pathlib import Path
import ast

source = Path("contracts/commit.py").read_text()
tree = ast.parse(source)

required_constants = (
    'DECISION_ENVELOPE = "commit-decision-v3"',
    'RECEIPT_SCHEMA = "commit-mission-receipt-v2"',
    'MANIFEST_SCHEMA = "commit-mission-manifest-v2"',
)

for value in required_constants:
    if source.count(value) != 1:
        raise SystemExit("STOP: contract constant boundary changed: " + value)

for name in ("get_mission_receipt", "get_mission_manifest"):
    node = next(
        n
        for n in ast.walk(tree)
        if isinstance(n, ast.FunctionDef) and n.name == name
    )

    ret = next(
        n
        for n in ast.walk(node)
        if isinstance(n, ast.Return)
    )

    if not isinstance(ret.value, ast.Dict):
        raise SystemExit("STOP: artifact return shape changed")

    keys = [
        key.value
        for key in ret.value.keys
        if isinstance(key, ast.Constant) and isinstance(key.value, str)
    ]

    if keys.count("evidence_root") != 1:
        raise SystemExit("STOP: sealed root projection changed")

    if keys.count("evaluation_evidence_root") != 1:
        raise SystemExit("STOP: active root projection changed")

    idx = keys.index("evaluation_evidence_root")
    expr = ast.unparse(ret.value.values[idx])

    if expr != "self.mission_evaluation_evidence_root[mission_id]":
        raise SystemExit("STOP: evaluation root binding changed")

print("REVIEWER_ARTIFACT_BINDING=EXACT")
PY2

SEALED_ROOT_WRITES="$(
  grep -c 'self\.mission_evidence_root\[mission_id\] =' contracts/commit.py
)"

echo "SEALED_ROOT_WRITE_COUNT=$SEALED_ROOT_WRITES"
test "$SEALED_ROOT_WRITES" = "2"

git diff --check

echo
echo "COMMIT_STEP2_REVIEWER_HARD_GATES_CERTIFICATION=PASS"
echo "DETERMINISTIC_TESTS=35/35_PASS"
echo "RUNTIME_TESTS=113/113_PASS"
echo "FULL_SUITE=148/148_PASS"
echo "REVIEWER_HARD_GATES=11/11_PASS"
echo "REPAIR_TESTS=18/18_PASS"
echo "ACTIVE_ROOT_RUNTIME_VECTOR=1/1_PASS"
echo "DEADLINE_ALLOCATION_RACE_TESTS=4/4_PASS"
echo "FEE_POLICY_TESTS=5/5_PASS"
echo "FEE_POLICY_BINDING=EXACT"
echo "FEE_PROFILE_STATUS=TARGET_NETWORK_REQUIRED"
echo "NUMERIC_NETWORK_FEE_QUOTE=NOT_CLAIMED"
echo "CONTRACT_SPEC_EVIDENCE_ROOT_PARITY=PASS"
echo "DECISION_ENVELOPE=commit-decision-v3"
echo "RECEIPT_SCHEMA=commit-mission-receipt-v2"
echo "MANIFEST_SCHEMA=commit-mission-manifest-v2"
echo "CONTRACT_SHA=$EXPECTED_CONTRACT_SHA"
echo "PROVENANCE_MODEL_SHA=$EXPECTED_PROVENANCE_MODEL_SHA"
echo "ONCHAIN_MODEL_SHA=$EXPECTED_ONCHAIN_MODEL_SHA"
echo "RUNTIME_ARCHIVE_SHA=$ACTUAL_RUNTIME_SHA"
echo "FEE_POLICY_SHA=$EXPECTED_FEE_POLICY_SHA"
echo "FEE_POLICY_TEST_SHA=$EXPECTED_FEE_POLICY_TEST_SHA"
