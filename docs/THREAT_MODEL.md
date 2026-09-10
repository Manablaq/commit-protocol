# Threat Model and Verification Status

Status: hardened source and direct-runtime tests pass locally. Network-
dependent controls remain unverified and are not presented as production
guarantees.

| Threat | Current control | Remaining limitation / proof |
| --- | --- | --- |
| Unauthorized supplier | Mission-scoped allowlist; only principal or authorized supplier can prepare | Supplier identity is an authenticated address, not proof of an off-chain company identity |
| Effect substitution | Immutable effect fields; canonical root includes dependency, supplier, beneficiary, value, expiry, and digest | Digest commits to an external payload; the payload is not stored on chain |
| Cyclic dependency | Single-parent graph; dependency must already exist; bounded seal-time walk checks every chain | This revision supports a bounded single-parent graph, not arbitrary DAG/nested missions |
| Evidence substitution | HTTPS host/path boundary, active authority, mission subject, exact URL, v2 snapshot binding, digest and expiry | Final redirect destination and issuer key ownership are not verified |
| Ambiguous evidence parsing | 16 KiB body cap; strict top-level schema; duplicate-key and non-standard-number rejection; canonical payload hashing | The source still must provide an authoritative, stable record before the expiry boundary |
| Authority failure | Owner can deactivate an authority for new evidence; sealing rejects duplicate origin/path labels | Origin/path equality still does not prove independent organizations; deactivation can strand a sealed mission until recovery |
| Prompt injection | Evidence is parsed as fixed data; only the configured web reads are used | No LLM reasoning is currently used; arbitrary natural-language policy is not supported |
| Leader manipulation | Validator re-reads evidence and compares the bound decision envelope | Live validator consensus proof is still required |
| Replay / double allocation | Exact nonce, self-sender check, terminal allocation flag, harmless late callback | Live finality and cross-network ordering are unverified |
| Trapped mission funds | Permissionless recovery after the recovery deadline | Recovery still requires network liveness, a funded caller, and a successful transaction |
| Failed external payment | Entitlement is consumed before dispatch to prevent double payment | No authenticated delivery/non-delivery proof or retry exists; `DISPATCHED` value can remain unresolved |
| Fee exhaustion | Mission budget and funding are bounded independently from effect amounts | Target-network fee profile and separate fee reserve are not implemented |
| Oversized remote input | 16 KiB body cap and 128-character reason cap | Full target-network resource/fee measurements are still required |

## Explicit non-claims

COMMIT does not roll back arbitrary websites, APIs, blockchains, or physical
actions. Its atomic boundary is allocation of internal settlement entitlements
after a successful finalized decision. External transfers are asynchronous and
remain a separate payment-progress state.

## Release blockers

1. Deploy the exact source to Studio Dev using its matching v0.6 RC toolchain.
2. Prove `FINISHED_WITH_RETURN` for creation, funding, evaluation, finalized
   callback allocation, claims, and recovery.
3. Profile and record fees for every write and child-message branch.
4. Close redirect provenance with a verified final-URL capability or implement
   and test issuer-key signatures.
5. Add an authenticated external-transfer reconciliation mechanism before
   treating native-GEN custody as production-ready.
