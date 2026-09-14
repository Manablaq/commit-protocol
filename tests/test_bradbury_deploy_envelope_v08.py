import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "contracts/commit.py"
MAX_BRADBURY_SOURCE_BYTES = 49152


def test_bradbury_deploy_source_stays_within_certified_envelope():
    raw = CONTRACT.read_bytes()

    assert len(raw) <= MAX_BRADBURY_SOURCE_BYTES
    assert raw.startswith(
        b'# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }'
    )

    ast.parse(raw.decode("utf-8"))
