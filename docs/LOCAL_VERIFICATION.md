# Local Verification Record

Verified 2026-09-10. This record covers deterministic and direct-runtime checks only. It is not evidence of validator consensus, network finality, deployment, custody safety, or on-chain correctness.

## Pinned inputs

- Python: 3.12.14
- `genlayer-py`: 0.19.0rc2
- `genlayer-test`: 0.30.0rc2
- `genvm-linter`: 0.11.1rc2
- GenVM manager release: v0.6.0-rc4
- Runtime archive SHA-256: `bd30580f911338d5533460eca8ed714dec371de5803c04e41dbb96430aea7b6e`
- Contract runner used for the Bradbury-compatible source path: `py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6`
- Standard library dependency: `py-lib-genlayer-std:11rhn002yfajawsz7fai6mykznbxkxs6l91iskj5cm82c92qhy3v`
- The manager archive also contains the current v0.6 runner `5jyc...`; a Bradbury canary showed that runner is unavailable there and is not used by the contract.

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
- Deterministic models, commitment references, and provenance rules: 23 tests passed.
- Direct-runtime registry, callback, independent-evaluation, provenance, native-GEN funding, allocation, recovery-race, and claim-dispatch tests: 53 tests passed against the extracted legacy runner path from a cleared SDK cache.
- Whitespace validation: passed.

The contract tests establish principal-bound mission creation, payable native-GEN funding, on-chain intent commitment derivation, deadline ordering, preparation deadline enforcement, budget bounds, owner-controlled authority registration, exact URL/path provenance checks, mission-bound evidence, distinct-authority sealing, digest validation, duplicate rejection, sealed-state immutability, finality-gated decision application, atomic effect/refund entitlement allocation, recovery winning against a late callback, one-way claim dispatch, explicit deadline recovery, and honest capability disclosure. The reference commitment and provenance tests establish Python parity for the contract's Keccak-256, framed intent/effect/evidence encoding and adversarial URL cases. Expiry uses the transaction-pinned standard-library clock documented by GenLayer. The callback tests establish the generated zero-value `finalized` message payload and deterministic guards for sender authentication, identifier binding, and idempotence. The independent-evaluation tests establish exact schema/payload-hash checks, bounded decisions from two independently re-read sources, rejection of forged leader output, rejection of changed validator evidence, and single-use evaluation. Direct mode executes the leader locally and captures the validator for a separate test invocation; it does not establish live network consensus, live finality delivery, live fee behavior, external transfer failure recovery, or final redirect provenance.
