# Threat model and verification status

Status: the reviewer-hardening candidate passes local static, Direct Runtime,
backend, frontend, and browser verification. The exact coordinator is finalized
and byte-matched on Studio Next, with fresh COMMIT and ABORT lifecycle proofs.
Production frontend rebinding is complete. Downstream external-transfer
reconciliation remains explicitly bounded work.

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
| Leader manipulation | Validator path is bound to the consequential evidence result | Fresh current-source COMMIT and ABORT consensus proofs passed; recovery/stale-callback hosted proof remains separately certifiable |
| Replay/double allocation | Decision nonce, exact roots, self-callback authentication, terminal allocation flag, recovery race guards | Fresh current-source COMMIT and ABORT callback/claim proofs passed; recovery/stale-callback hosted proof remains separately certifiable |
| Trapped funds | Permissionless recovery after declared recovery deadline | Requires network liveness and a successful recovery transaction |
| Indirect claim/reentrancy-style caller confusion | Public claim requires immediate sender == original transaction submitter; entitlement is consumed before dispatch | Downstream chain-layer delivery/reconciliation is outside COMMIT's proven atomic boundary |
| Fee exhaustion | Fee policy enumerates all message-producing paths and invalidation conditions | Exact live quotes are required before each new message path; the certified deployment and tested lifecycle used measured current-network values |
| Oversized remote input | 16 KiB response cap and bounded text/reason/graph fields | Target-network resource behavior must still be certified |

## Settlement boundary

COMMIT's security guarantee is the allocation and one-time consumption of
protocol-held settlement rights after a finalized exact decision. Native GEN
dispatch is an external finalization message to the chain layer.

For Agent Tank, COMMIT will prove the EOA claim/refund paths it actually uses.
It does not represent generic EVM-contract delivery, downstream application
success, or automatic reconciliation as part of semantic atomicity.

## Remaining bounded items

1. Keep downstream GEN delivery/retry/reconciliation explicitly outside the
   guarantee unless a native, authenticated delivery receipt and safe retry
   protocol is added and separately proven.
2. Complete hosted recovery/stale-callback proof if a future submission requires
   that additional live evidence; local state-machine and runtime coverage is
   already present.

The repository's GitHub Actions `Verification` workflow is active. Run
`35134050898` completed successfully for the deployed source commit
`8726ce7924fd78281a117b92ce4733396501ebac`.
