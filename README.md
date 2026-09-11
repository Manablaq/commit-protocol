# COMMIT

**A protocol for decentralized semantic atomicity in autonomous economic workflows.**

Databases made data atomic. Blockchains made code atomic. COMMIT makes autonomous intentions atomic.

COMMIT coordinates a mission whose participants, evidence, deadlines, and proposed economic effects are fixed before adjudication. GenLayer validators determine whether the mission's semantic acceptance predicate has been satisfied. Only a successful final decision can allocate the mission's registered settlement rights inside the protocol.

The reference implementation will demonstrate autonomous procurement: independent suppliers prepare offers and evidence, while COMMIT decides whether the assembled package satisfies the buyer's complete intent.

## Exact guarantee

COMMIT does **not** claim to roll back arbitrary external systems or make asynchronous cross-contract effects synchronously atomic. Its enforceable guarantee is narrower and testable:

> For assets escrowed in the COMMIT coordinator, settlement entitlements are allocated as one state transition only after a successful GenLayer decision reaches the required finality. Otherwise, the mission follows its declared abort or compensation path.

External effects must be represented as reversible reservations, idempotent adapters, or explicitly compensatable actions. They are never described as magically reversible.

## Current status

The product thesis, protocol specification, accounting model, state machine, evidence model, and adversarial review are drafted. The contract requires explicit supplier authorization, rejects duplicate authority labels for the same registered origin/path, validates canonical DNS-style hosts and path prefixes, rejects boolean/out-of-range uint inputs, uses a bounded single-parent acyclic effect graph with seal-time cycle checks, accepts only the explicit `all-evidence-and-effects-v1` policy, binds every fetched record to the mission/objective/policy/intent/effect snapshot, rejects missing or malformed bodies, rejects ambiguous/non-standard JSON, and limits remote evidence bodies to 16 KiB. Revision `0.7.0-reviewable-manifest` adds a bounded reviewer-facing mission manifest that combines the frozen mission terms, exact root inputs, roots, and authority metadata in one read, plus overflow-guarded counters on top of the v0.6 semantic receipt and lifecycle hardening. Revision `0.7.0` passes GenVM lint, 24 deterministic tests, and 79 direct-runtime tests. It is deployed source-matched on Studio Dev at `0x10c708517b4465596E2dc40De92B30A610Cb7a10`; the exact deployment and live COMMIT/ABORT proofs are recorded in [DEPLOYMENT_LOG_STUDIO_DEV.md](./docs/DEPLOYMENT_LOG_STUDIO_DEV.md). Studio Dev exposes finalized external dispatch children but not a delivery/non-delivery proof, so independent delivery reconciliation and external-transfer recovery remain unproven and are explicitly disabled. The historical Bradbury canary proved that this v0.6 runner is unavailable on Bradbury; its separate legacy probe is not evidence for the current source.

The current reviewer-hard-gates candidate adds authenticated issuer-address attestations, immutable authority/version and evidence-record/version identity, mission-version and freshness binding, expiry through the recovery deadline, distinct authenticated-issuer corroboration, and exact v2 contract/reference-model evidence-root parity. These candidate changes are locally certified but are not the historical v0.7 Studio Dev deployment. Any network proof for this candidate requires a fresh source-matched contract deployment; COMMIT does not claim an in-place upgrade of the historical deployed contract.

See [PRODUCT_THESIS.md](./docs/PRODUCT_THESIS.md), [ENVIRONMENT.md](./docs/ENVIRONMENT.md), and [VERIFICATION_POLICY.md](./docs/VERIFICATION_POLICY.md).

Reproduce the current local checks with the exact commands and runtime digest in [LOCAL_VERIFICATION.md](./docs/LOCAL_VERIFICATION.md).

## Protocol design and open gates

- [Semantic atomicity](./docs/SEMANTIC_ATOMICITY.md): objects, consequence binding and guarantee boundary.
- [Accounting](./docs/ACCOUNTING_MODEL.md): conservation, escrow, refunds and in-flight payments.
- [State machine](./docs/STATE_MACHINE.md): roles, transitions and recovery races.
- [Evidence and consensus](./docs/EVIDENCE_MODEL.md): publisher authority, freshness and independent evaluation.
- [Studio Dev fee runbook](./docs/STUDIO_DEV_FEE_RUNBOOK.md): message-aware fee estimation and verification rules.
- [Threat model](./docs/THREAT_MODEL.md): adversarial cases and unresolved high-severity findings.
- [Verification gates](./docs/OPEN_QUESTIONS.md): evidence still required before custody implementation.

## Build order

1. Protocol specification and invariants
2. Threat model and state machine
3. Intelligent Contract implementation
4. Deterministic tests and adversarial tests
5. GenLayer consensus tests and fee profiling
6. Studio Dev deployment and source/receipt verification with the matching v0.6 RC stack — v0.7 source match recorded at `0x10c708...7a10`
7. Native-GEN custody, finality-gated allocation, finalized claim dispatch, reviewer manifest proof, and both COMMIT/ABORT branches on Studio Dev — missions 008 and 009 recorded
8. Backend/indexer integration
9. Frontend only after the backend gate passes
10. Bradbury compatibility check and persistent production-like validation

## Official references

- [GenLayer networks](https://docs.genlayer.com/developers/networks)
- [Consensus v0.6 migration](https://docs.genlayer.com/developers/consensus-v06-migration)
- [Messages](https://docs.genlayer.com/developers/intelligent-contracts/features/messages)
- [Value transfers](https://docs.genlayer.com/developers/intelligent-contracts/features/value-transfers)
- [Fee profiling and estimation](https://docs.genlayer.com/developers/decentralized-applications/fee-profiling-and-estimation)
- [Agent Tank Hackathon](https://portal.genlayer.foundation/agent-tank/)
