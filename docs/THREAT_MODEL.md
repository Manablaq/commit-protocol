# Threat model and verification status

Status: final reviewer-hardening candidate passes local static, Direct Runtime,
backend, frontend, and browser verification. Fresh hosted preview and GenLayer
deployment certification are still pending.

| Threat | Current control | Remaining limitation / proof |
| --- | --- | --- |
| Unauthorized supplier | Mission-scoped allowlist | Address authentication is not off-chain company identity |
| Effect substitution | Immutable effect fields and exact root binding | External payload itself is committed by digest rather than fully stored |
| Evidence substitution | Authority/version + issuer + record/version + mission/version + URL + digest + time binding | Registered issuer identity remains the trust root |
| Future/stale evidence | Publication must be within mission lifetime and no later than transaction time; expiry must cover recovery | Host wall-clock time is intentionally not used |
| Redirect/provenance ambiguity | Exact issuer-authenticated record digest and mission/version remain mandatory even if HTTP transport redirects | Final redirect URL itself is not exposed as a separate on-chain field |
| False corroboration | Seal requires distinct authenticated issuer addresses | Distinct addresses do not prove independent organizations |
| Acquisition/integrity failure | Persist `REPAIR_REQUIRED`; only authenticated newer same-record successor may repair before recovery | Network/issuer availability is still required |
| Prompt injection | Current reference policy parses a fixed structured schema and uses no LLM inference | Arbitrary natural-language policy is intentionally out of scope |
| Leader manipulation | Validator path is bound to the consequential evidence result | Fresh live current-source consensus proof is still required |
| Replay/double allocation | Decision nonce, exact roots, self-callback authentication, terminal allocation flag, recovery race guards | Fresh current-source live lifecycle proof is still required |
| Trapped funds | Permissionless recovery after declared recovery deadline | Requires network liveness and a successful recovery transaction |
| Indirect claim/reentrancy-style caller confusion | Public claim requires immediate sender == original transaction submitter; entitlement is consumed before dispatch | Downstream chain-layer delivery/reconciliation is outside COMMIT's proven atomic boundary |
| Fee exhaustion | Fee policy enumerates all message-producing paths and invalidation conditions | Exact candidate/network numeric estimates must be measured before deployment |
| Oversized remote input | 16 KiB response cap and bounded text/reason/graph fields | Target-network resource behavior must still be certified |

## Settlement boundary

COMMIT's security guarantee is the allocation and one-time consumption of
protocol-held settlement rights after a finalized exact decision. Native GEN
dispatch is an external finalization message to the chain layer.

For Agent Tank, COMMIT will prove the EOA claim/refund paths it actually uses.
It does not represent generic EVM-contract delivery, downstream application
success, or automatic reconciliation as part of semantic atomicity.

## Remaining pre-submission gates

1. Measure exact target-network fees/message allocations for the hardened
   coordinator.
2. Prove the existing helper address, deployed helper bytes, and constructor
   binding read-only; redeploy helper only if that proof fails.
3. Deploy the exact `e235731ac223ee136b06b8cfc332065927a03553a3b1f5531571cd4d5da119c6` coordinator candidate and prove finality,
   execution success, and byte-for-byte source identity.
4. Execute fresh current-source COMMIT, ABORT, recovery/stale-callback, and EOA
   claim/refund certification.
5. Deploy the application candidate to an isolated preview and prove the real
   `/verify` index/transaction paths, security headers, wallet behavior, and
   browser E2E before production promotion.
6. Publish a durable reviewer-inspectable evidence packet and then update the
   final Agent Tank proof map.
