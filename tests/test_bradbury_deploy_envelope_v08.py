import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "contracts/commit.py"

EXPECTED_SOURCE_BYTES = 19914
EXPECTED_RUNNER_HEADER = (
    b'# { "Depends": '
    b'"py-genlayer:5jycge4q8k23462jtb0b9fyey1s9qz928sz2nbrd9mg4sxqg2qng" }'
)


def test_studio_dev_deploy_source_matches_hardened_candidate_shape():
    raw = CONTRACT.read_bytes()

    assert len(raw) == EXPECTED_SOURCE_BYTES
    assert raw.startswith(EXPECTED_RUNNER_HEADER)

    ast.parse(raw.decode("utf-8"))
