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

The product thesis, protocol specification, accounting model, state machine, evidence model, and adversarial review are drafted. The deterministic settlement, commitment, and provenance models pass 23 tests. The non-payable mission-registry, finalized-message, independent-evaluation, and provenance probes pass GenVM lint and 42 direct-runtime tests against the pinned v0.6 runner. The registry computes the mission intent digest from stored terms, bounds effects by preparation deadline and budget, and derives evidence roots from owner-registered HTTPS authorities and mission-bound records. These are local results only: live finality delivery, failure recovery, custody, redirect/final-destination enforcement, and runtime compatibility remain unproven. The COMMIT custody contract has not been deployed and no on-chain correctness claim exists yet.

See [PRODUCT_THESIS.md](./docs/PRODUCT_THESIS.md), [ENVIRONMENT.md](./docs/ENVIRONMENT.md), and [VERIFICATION_POLICY.md](./docs/VERIFICATION_POLICY.md).

Reproduce the current local checks with the exact commands and runtime digest in [LOCAL_VERIFICATION.md](./docs/LOCAL_VERIFICATION.md).

## Protocol design and open gates

- [Semantic atomicity](./docs/SEMANTIC_ATOMICITY.md): objects, consequence binding and guarantee boundary.
- [Accounting](./docs/ACCOUNTING_MODEL.md): conservation, escrow, refunds and in-flight payments.
- [State machine](./docs/STATE_MACHINE.md): roles, transitions and recovery races.
- [Evidence and consensus](./docs/EVIDENCE_MODEL.md): publisher authority, freshness and independent evaluation.
- [Threat model](./docs/THREAT_MODEL.md): adversarial cases and unresolved high-severity findings.
- [Verification gates](./docs/OPEN_QUESTIONS.md): evidence still required before custody implementation.

## Build order

1. Protocol specification and invariants
2. Threat model and state machine
3. Intelligent Contract implementation
4. Deterministic tests and adversarial tests
5. GenLayer consensus tests and fee profiling
6. Preview-network deployment and full receipt verification
7. Bradbury compatibility check and deployment, if the v0.6 stack is supported there
8. Backend/indexer integration
9. Frontend only after the backend gate passes

## Official references

- [GenLayer networks](https://docs.genlayer.com/developers/networks)
- [Consensus v0.6 migration](https://docs.genlayer.com/developers/consensus-v06-migration)
- [Messages](https://docs.genlayer.com/developers/intelligent-contracts/features/messages)
- [Value transfers](https://docs.genlayer.com/developers/intelligent-contracts/features/value-transfers)
- [Fee profiling and estimation](https://docs.genlayer.com/developers/decentralized-applications/fee-profiling-and-estimation)
- [Agent Tank Hackathon](https://portal.genlayer.foundation/agent-tank/)
