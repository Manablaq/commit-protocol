#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

EXPECTED_RUNTIME_SHA="bd30580f911338d5533460eca8ed714dec371de5803c04e41dbb96430aea7b6e"
EXPECTED_CONTRACT_SHA="f63756be39755b6e2f41329dfd046f628b3e44bcff392579d7d1ffc827fe75f9"
EXPECTED_MODEL_SHA="335a3d8f2f672c64657dc3a90eda964776c5b5d8399006455eb47dea5f5bcff7"
EXPECTED_LEGACY_SHA="9f4935d86c65a3642d224824575e0fc7957eebb35e089a19ce85233fda8c81a6"
EXPECTED_PROVENANCE_TEST_SHA="f29e50a2156806eac774516e256f3c8d069abe645f5ac103da1721d0ab1604d0"
EXPECTED_HARD_GATE_SHA="bbb04e2c004a071ac99c8ae067c265e058e7b0fdaa88b6e9e6bdb732f4baad21"

: "${GENVM_PREBUILT_DIR:?Set GENVM_PREBUILT_DIR to the verified extracted v0.6.0-rc3 release tree}"
: "${GENVM_ARCHIVE:?Set GENVM_ARCHIVE to the verified v0.6.0-rc3 genvm-universal archive}"

test -d "$GENVM_PREBUILT_DIR"
test -f "$GENVM_PREBUILT_DIR/.extracted"
test -f "$GENVM_ARCHIVE"

ACTUAL_RUNTIME_SHA="$(
  shasum -a 256 "$GENVM_ARCHIVE" |
  awk '{print $1}'
)"

ACTUAL_CONTRACT_SHA="$(
  shasum -a 256 contracts/commit.py |
  awk '{print $1}'
)"

ACTUAL_MODEL_SHA="$(
  shasum -a 256 spec_model/provenance.py |
  awk '{print $1}'
)"

ACTUAL_LEGACY_SHA="$(
  shasum -a 256 tests/runtime/test_commit_skeleton.py |
  awk '{print $1}'
)"

ACTUAL_PROVENANCE_TEST_SHA="$(
  shasum -a 256 tests/test_provenance.py |
  awk '{print $1}'
)"

ACTUAL_HARD_GATE_SHA="$(
  shasum -a 256 tests/runtime/test_reviewer_hard_gates_v08.py |
  awk '{print $1}'
)"

echo "EXPECTED_RUNTIME_SHA=$EXPECTED_RUNTIME_SHA"
echo "ACTUAL_RUNTIME_SHA=$ACTUAL_RUNTIME_SHA"

echo "EXPECTED_CONTRACT_SHA=$EXPECTED_CONTRACT_SHA"
echo "ACTUAL_CONTRACT_SHA=$ACTUAL_CONTRACT_SHA"

echo "EXPECTED_MODEL_SHA=$EXPECTED_MODEL_SHA"
echo "ACTUAL_MODEL_SHA=$ACTUAL_MODEL_SHA"

echo "EXPECTED_LEGACY_SHA=$EXPECTED_LEGACY_SHA"
echo "ACTUAL_LEGACY_SHA=$ACTUAL_LEGACY_SHA"

echo "EXPECTED_PROVENANCE_TEST_SHA=$EXPECTED_PROVENANCE_TEST_SHA"
echo "ACTUAL_PROVENANCE_TEST_SHA=$ACTUAL_PROVENANCE_TEST_SHA"

echo "EXPECTED_HARD_GATE_SHA=$EXPECTED_HARD_GATE_SHA"
echo "ACTUAL_HARD_GATE_SHA=$ACTUAL_HARD_GATE_SHA"

test "$ACTUAL_RUNTIME_SHA" = "$EXPECTED_RUNTIME_SHA"
test "$ACTUAL_CONTRACT_SHA" = "$EXPECTED_CONTRACT_SHA"
test "$ACTUAL_MODEL_SHA" = "$EXPECTED_MODEL_SHA"
test "$ACTUAL_LEGACY_SHA" = "$EXPECTED_LEGACY_SHA"
test "$ACTUAL_PROVENANCE_TEST_SHA" = "$EXPECTED_PROVENANCE_TEST_SHA"
test "$ACTUAL_HARD_GATE_SHA" = "$EXPECTED_HARD_GATE_SHA"

uv sync --frozen

uv run genvm-lint lint contracts/commit.py
uv run genvm-lint validate contracts/commit.py
uv run genvm-lint typecheck contracts/commit.py
uv run genvm-lint schema contracts/commit.py >/tmp/commit-step2-schema.txt
uv run genvm-lint check contracts/commit.py

uv run python -m pytest -q \
  tests/test_canonical.py \
  tests/test_onchain_encoding.py \
  tests/test_provenance.py \
  tests/test_settlement_model.py

GENVM_PREBUILT_DIR="$GENVM_PREBUILT_DIR" \
uv run python -m pytest \
  -q tests/runtime

GENVM_PREBUILT_DIR="$GENVM_PREBUILT_DIR" \
uv run python -m pytest \
  -q tests/runtime/test_reviewer_hard_gates_v08.py

GENVM_PREBUILT_DIR="$GENVM_PREBUILT_DIR" \
uv run python -m pytest \
  -q \
  tests/runtime/test_commit_skeleton.py::test_supplier_prepares_effect_and_principal_seals_snapshot

DETERMINISTIC_COUNT="$(
  uv run python -m pytest \
    --collect-only -q \
    tests/test_canonical.py \
    tests/test_onchain_encoding.py \
    tests/test_provenance.py \
    tests/test_settlement_model.py 2>/dev/null |
  grep -Eo '[0-9]+ tests? collected' |
  tail -1 |
  grep -Eo '^[0-9]+'
)"

RUNTIME_COUNT="$(
  GENVM_PREBUILT_DIR="$GENVM_PREBUILT_DIR" \
  uv run python -m pytest \
    --collect-only -q tests/runtime 2>/dev/null |
  grep -Eo '[0-9]+ tests? collected' |
  tail -1 |
  grep -Eo '^[0-9]+'
)"

HARD_GATE_COUNT="$(
  GENVM_PREBUILT_DIR="$GENVM_PREBUILT_DIR" \
  uv run python -m pytest \
    --collect-only -q \
    tests/runtime/test_reviewer_hard_gates_v08.py 2>/dev/null |
  grep -Eo '[0-9]+ tests? collected' |
  tail -1 |
  grep -Eo '^[0-9]+'
)"

echo "DETERMINISTIC_COUNT=$DETERMINISTIC_COUNT"
echo "RUNTIME_COUNT=$RUNTIME_COUNT"
echo "HARD_GATE_COUNT=$HARD_GATE_COUNT"

test "$DETERMINISTIC_COUNT" = "26"
test "$RUNTIME_COUNT" = "90"
test "$HARD_GATE_COUNT" = "11"

git diff --check

echo
echo "COMMIT_STEP2_REVIEWER_HARD_GATES_CERTIFICATION=PASS"
echo "DETERMINISTIC_TESTS=26/26_PASS"
echo "RUNTIME_TESTS=90/90_PASS"
echo "REVIEWER_HARD_GATES=11/11_PASS"
echo "CONTRACT_SPEC_EVIDENCE_ROOT_PARITY=PASS"
echo "CONTRACT_SHA=$ACTUAL_CONTRACT_SHA"
echo "SPEC_MODEL_SHA=$ACTUAL_MODEL_SHA"
echo "HARD_GATE_TEST_SHA=$ACTUAL_HARD_GATE_SHA"
echo "RUNTIME_ARCHIVE_SHA=$ACTUAL_RUNTIME_SHA"
