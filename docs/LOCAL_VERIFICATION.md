# Local Verification Record

Verified 2026-09-11. This record covers deterministic and direct-runtime checks only. It is not evidence of validator consensus, network finality, deployment, custody safety, or on-chain correctness.

## Pinned inputs

- Python: 3.12.14
- `genlayer-py`: 0.19.0rc2
- `genlayer-test`: 0.30.0rc2
- `genvm-linter`: 0.11.1rc2
- GenVM manager Direct-runtime baseline: v0.6.0-rc3
- Runtime archive SHA-256: `bd30580f911338d5533460eca8ed714dec371de5803c04e41dbb96430aea7b6e`
- Contract runner used by the Studio Dev-targeted source: `py-genlayer:5jycge4q8k23462jtb0b9fyey1s9qz928sz2nbrd9mg4sxqg2qng`
- Standard library dependency resolved by that runner: `py-lib-genlayer-std:kzr02ndm9et4qkmbqpq5djjt5sme2yt76n7sz1qbzax0knt6mam0`
- The manager archive also contains Bradbury's documented legacy runner `1jb45...`; a historical canary showed the v0.6 runner is unavailable there. The current source does not target that legacy path.

Python dependencies are locked in `uv.lock`. The runtime archive is intentionally not committed because of its size; verify its digest before extracting it.

## Commands

After extracting the verified archive to a directory, set `GENVM_PREBUILT_DIR` to that directory, not to the `.tar.xz` file.

```sh
uv run genvm-lint check contracts/commit.py
uv run genvm-lint check probes/independent_evaluation.py
uv run genvm-lint check probes/finalized_callback.py
uv run python -m pytest -q tests/test_canonical.py tests/test_onchain_encoding.py tests/test_provenance.py tests/test_settlement_model.py
GENVM_PREBUILT_DIR=/absolute/path/to/verified/v0.6.0-rc3-tree uv run python -m pytest -q tests/runtime
git diff --check
```

## Result

- GenVM lint: 3 checks passed.
- Deterministic models, commitment references, and provenance rules: 24 tests passed.
- Direct-runtime registry, callback, independent-evaluation, provenance, supplier authorization, duplicate-origin rejection, canonical authority validation, strict evidence JSON, bounded graph, native-GEN funding, allocation, recovery-race, claim-dispatch, permissionless evaluation, full decision-envelope comparison, mission-scoped entitlement reads, mission receipt, reviewer manifest, explicit timeout/cancellation decisions, guarded counters, and indexed-read-surface tests: 79 tests passed against the extracted v0.6 RC runner and modern package layout from a cleared SDK cache; the deterministic suite adds 24 passing tests (103 total test invocations).
- Whitespace validation: passed.

The contract tests establish principal-bound mission creation, explicit versioned policy enforcement, payable native-GEN funding, chain/deployment-bound intent commitment derivation, deadline ordering, preparation deadline enforcement, budget bounds, owner-controlled active authority registration, exact URL/path provenance checks, mission-bound v2 evidence, distinct-authority sealing, authorized supplier preparation, bounded single-parent graph validation, digest validation, duplicate rejection, sealed-state immutability, permissionless post-seal evaluation, finality-gated decision application, atomic effect/refund entitlement allocation, overflow-guarded counters, explicit cancellation/timeout ABORT receipts, recovery winning against a late callback, one-way claim dispatch, explicit deadline recovery, reviewer manifest reconstruction, and honest capability disclosure. The reference commitment and provenance tests establish Python parity for the contract's Keccak-256, framed intent/effect/evidence encoding and adversarial URL cases. Expiry uses the transaction-pinned standard-library clock documented by GenLayer. The callback tests establish the generated zero-value `finalized` message payload and deterministic guards for sender authentication, identifier binding, and idempotence. The independent-evaluation tests establish exact v2 schema/snapshot/payload-hash checks, full consequential-envelope comparison, bounded decisions from independently re-read sources, rejection of forged leader output, rejection of changed validator evidence, oversized input rejection, and single-use evaluation. Direct mode executes the leader locally and captures the validator for a separate test invocation; it does not establish live network consensus, live finality delivery, live fee behavior, external transfer failure recovery, or final redirect provenance.

## Live Studio Dev verification

The source-matched v0.7 deployment and transaction evidence are recorded in
[`DEPLOYMENT_LOG_STUDIO_DEV.md`](./DEPLOYMENT_LOG_STUDIO_DEV.md). The live
proof covers both policy outcomes on the same deployed bytecode:

- Mission 008 fetched two bound public records and returned `COMMIT`; its
  finalized self-callback allocated the prepared entitlement, and its claim
  consumed the entitlement exactly once.
- Mission 009 fetched one ineligible and one eligible record and returned
  `ABORT`; its finalized self-callback allocated the fixed refund, and its
  refund claim consumed that entitlement exactly once.

The first mission-008 evaluation intentionally remains documented as a failed
fee-allocation attempt. Its `fee no_matching_allocation` result led to the
message-aware fee runbook and the successful retry; it did not modify mission
state. These live fixtures prove contract behavior and public record binding,
not real-world issuer identity or authenticated external payment delivery.
