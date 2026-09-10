# Local Verification Record

Verified 2026-09-10. This record covers deterministic and direct-runtime checks only. It is not evidence of validator consensus, network finality, deployment, custody safety, or on-chain correctness.

## Pinned inputs

- Python: 3.12.14
- `genlayer-py`: 0.19.0rc2
- `genlayer-test`: 0.30.0rc2
- `genvm-linter`: 0.11.1rc2
- GenVM manager release: v0.6.0-rc4
- Runtime archive SHA-256: `bd30580f911338d5533460eca8ed714dec371de5803c04e41dbb96430aea7b6e`
- Contract runner: `py-genlayer:5jycge4q8k23462jtb0b9fyey1s9qz928sz2nbrd9mg4sxqg2qng`
- Standard library runner: `py-lib-genlayer-std:kzr02ndm9et4qkmbqpq5djjt5sme2yt76n7sz1qbzax0knt6mam0`

Python dependencies are locked in `uv.lock`. The runtime archive is intentionally not committed because of its size; verify its digest before extracting it.

## Commands

After extracting the verified archive to a directory, set `GENVM_PREBUILT_DIR` to that directory, not to the `.tar.xz` file.

```sh
.venv/bin/genvm-lint contracts/commit.py
.venv/bin/genvm-lint probes/finalized_callback.py
.venv/bin/python -m unittest discover -s tests -p 'test_*.py'
GENVM_PREBUILT_DIR=/absolute/path/to/extracted/genvm .venv/bin/pytest -q tests/runtime
git diff --check
```

## Result

- GenVM lint: 3 checks passed.
- Deterministic models: 17 tests passed.
- Direct-runtime skeleton and callback probes: 30 tests passed from a cleared SDK cache.
- Whitespace validation: passed.

The contract tests establish non-payable mission creation, principal binding, deadline ordering, digest validation, duplicate rejection, sealed-state immutability, explicit deadline recovery, and honest capability disclosure. Expiry uses the transaction-pinned standard-library clock documented by GenLayer. The callback tests establish the generated zero-value `finalized` message payload and deterministic guards for sender authentication, identifier binding, and idempotence. They deliberately impersonate the self-message in direct mode and therefore do not establish that a live network delivered or finalized it.
