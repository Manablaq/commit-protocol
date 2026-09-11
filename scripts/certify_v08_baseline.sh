#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

EXPECTED_RUNTIME_SHA="bd30580f911338d5533460eca8ed714dec371de5803c04e41dbb96430aea7b6e"
EXPECTED_CONTRACT_SHA="edfda0845b9590ee55cd6df35916ac40bb08d625467f7441625035cb55c16522"

: "${GENVM_PREBUILT_DIR:?Set GENVM_PREBUILT_DIR to the verified extracted v0.6.0-rc3 release tree}"
: "${GENVM_ARCHIVE:?Set GENVM_ARCHIVE to the verified v0.6.0-rc3 genvm-universal archive}"

test -d "$GENVM_PREBUILT_DIR"
test -f "$GENVM_PREBUILT_DIR/.extracted"
test -f "$GENVM_ARCHIVE"

ACTUAL_RUNTIME_SHA="$(shasum -a 256 "$GENVM_ARCHIVE" | awk '{print $1}')"
ACTUAL_CONTRACT_SHA="$(shasum -a 256 contracts/commit.py | awk '{print $1}')"

echo "EXPECTED_RUNTIME_SHA=$EXPECTED_RUNTIME_SHA"
echo "ACTUAL_RUNTIME_SHA=$ACTUAL_RUNTIME_SHA"
echo "EXPECTED_CONTRACT_SHA=$EXPECTED_CONTRACT_SHA"
echo "ACTUAL_CONTRACT_SHA=$ACTUAL_CONTRACT_SHA"

test "$ACTUAL_RUNTIME_SHA" = "$EXPECTED_RUNTIME_SHA"
test "$ACTUAL_CONTRACT_SHA" = "$EXPECTED_CONTRACT_SHA"

uv sync --frozen

uv run genvm-lint lint contracts/commit.py
uv run genvm-lint validate contracts/commit.py
uv run genvm-lint typecheck contracts/commit.py
uv run genvm-lint schema contracts/commit.py >/tmp/commit-v08-schema.txt
uv run genvm-lint check contracts/commit.py

uv run python -m pytest -q \
  tests/test_canonical.py \
  tests/test_onchain_encoding.py \
  tests/test_provenance.py \
  tests/test_settlement_model.py

GENVM_PREBUILT_DIR="$GENVM_PREBUILT_DIR" \
uv run python -m pytest -q tests/runtime

git diff --check

echo
echo "COMMIT_V08_BASELINE_CERTIFICATION=PASS"
echo "DETERMINISTIC_TESTS=PASS"
echo "RUNTIME_TESTS=79/79_PASS"
echo "CONTRACT_SHA=$ACTUAL_CONTRACT_SHA"
echo "RUNTIME_ARCHIVE_SHA=$ACTUAL_RUNTIME_SHA"
