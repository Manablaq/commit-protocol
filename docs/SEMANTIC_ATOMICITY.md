# Semantic Atomicity Specification

Revision: implementation draft 0.4, 2026-09-11. This describes the hardened
v0.7 candidate and the prior source's verified mission-004 Studio Dev behavior; it is not a
claim that every production or external-payment property is complete. Runtime
assumptions are tracked in [OPEN_QUESTIONS.md](./OPEN_QUESTIONS.md).

## Transaction and authority domain

A semantic transaction is a tuple `(domain, mission, version, intent, policy, graph, evidence, funding, decision)`. The domain includes protocol revision, chain ID, coordinator address, and a deployment-specific namespace. Mission identity includes the principal and a never-reused nonce. All hashes use an explicit object-type domain separator.

All consequential terms are supplied and authorized before adjudication. The
current evaluator implements the explicit
`all-evidence-and-effects-v1` rule: it does not interpret an arbitrary policy
document or invoke an LLM. It cannot invent a recipient, amount, obligation,
or permission.

## Objects

| Object | Required binding |
| --- | --- |
| Mission | Identity, principal, intent, hard constraints, budget, refund beneficiary, allowed roles, evidence policy, time policy |
| Mission version | Monotonic revision of mutable preparation; no revision changes an already sealed snapshot |
| Effect | Unique ID, type, supplier, recipient, integer GEN amount, exact payload digest, prerequisites, authority scope, nonce, reservation terms |
| Effect graph | Canonically ordered effects with one optional earlier dependency; unique IDs, no cycles, every dependency exists |
| Prepare receipt | Authenticated on-chain call from the principal or an explicitly authorized supplier, bound into the effect root |
| Evidence record | Registered authority, stable record ID/version, source reference, publication time, observed digest, expiry, subject and claim bindings |
| Evidence root | Digest of the ordered validated evidence manifest; availability and truth are separate from hashing |
| Commit decision | Fixed decision envelope plus COMMIT, justified by all hard constraints and independent semantic evaluation |
| Abort decision | Same envelope plus ABORT; semantic failure or declared deterministic cancellation/timeout reason |
| Commit/abort certificate | Exact decision envelope plus verifiable successful finalized transaction provenance; a JSON file alone is not a certificate |
| Mission receipt | Frozen terms, decision, allocation entries, decision nonce, and separate payment-progress records exposed by `get_mission_receipt` |
| Review manifest | Bounded ordered effect/evidence inputs, sealed roots, and registered authority metadata exposed by `get_mission_manifest` |

Canonical encoding is implemented with printable-ASCII length-prefixed fields
and GenLayer's native Keccak-256 for `commit-intent-v2`,
`commit-effect-leaf-v1`, and `commit-effect-root-v1`; the Python reference is
tested against the same byte construction. JavaScript parity and production
schema compatibility remain separate gates.

## Consequence binding

Let `X = (domain, mission_id, version, intent_hash, policy_hash, effect_root, evidence_root, allocation_root, budget, decision_time_policy)`.

The deterministic contract constructs X from the sealed snapshot. A validator independently retrieves authority-bound evidence and evaluates the original mission. Equivalence requires agreement on the decision and the exact consequential envelope. Explanatory prose is not used for accounting or authority.

After sealing, evaluation is permissionless. This keeps the semantic decision
path live if the principal is offline; principal-only preparation, funding,
evidence registration, sealing, and cancellation rules remain unchanged.

For any accepted equivalent results `r1` and `r2`, `allocation(r1) = allocation(r2)`. This follows only if allocation is derived from the same sealed graph and the decision bit, with no leader-supplied payout fields trusted. Tests must substitute each consequential field and demonstrate rejection.

## Atomicity property

For a mission with funded escrow F and agreed payouts P:

- Before a valid finalized COMMIT authorizes allocation, supplier entitlements are zero.
- COMMIT allocates every agreed entitlement and the residual principal refund in one coordinator state transition.
- ABORT allocates zero supplier entitlements and makes F refundable to the fixed principal beneficiary.
- No mission may allocate both COMMIT and ABORT outcomes.
- Every subsequent withdrawal consumes an existing entitlement exactly once.

The atomic boundary is allocation of rights inside one coordinator. Separately finalized external transfers do not arrive simultaneously. A successful procurement commitment also does not prove future physical delivery; the mission must specify what is being purchased and at which stage payment becomes due.

## Effect classes

1. **Escrow allocation:** hard atomic within the coordinator's ledger. No arbitrary external call occurs in the allocation loop.
2. **Supplier reservation:** authenticated supplier commitment; its real-world enforcement depends on the supplier and declared remedy. A receipt is not proof of physical custody.
3. **Nested service commitment:** child identity, scope, budget, and outcome are bound to the parent. A dependency receipt from another contract is not automatically a shared atomic transaction. Same-coordinator atomic grouping requires separately proven group allocation; other arrangements are compensating workflows.

Unsupported external effect types must fail explicitly. A compensation plan identifies who owes what, deadline, funding source, and failure handling. Compensation can fail; it must not be described as rollback.

## Temporal semantics

GenLayer's execution clock uses the transaction timestamp, not validation completion time. Therefore a timestamp guard defines transaction-time eligibility only. It cannot guarantee that a physical reservation still exists when consensus finishes.

For the reference procurement workflow, a supplier must explicitly accept a reservation obligation tied to COMMIT's eventual terminal outcome, or provide an enforceable reservation adapter with tested expiry behavior. A short external expiry plus an assumed finality delay is insufficient. Deadline extension never silently extends supplier consent.

## Liveness assumptions

Recovery requires a functioning network, an available submitting party, adequate transaction fees, and an executable recovery transaction. No contract guarantees a fixed wall-clock completion during network failure. Recovery deadlines prevent application-level indefinite locks only under these assumptions. An unresolved external transfer cannot safely become refundable until non-payment is authenticated.
