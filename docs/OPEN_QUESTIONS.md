# Submission boundaries

COMMIT is explicit about what is already proven and what remains bounded for
Agent Tank submission.

## Proven locally for the hardening candidate

- coordinator source SHA-256 `e235731ac223ee136b06b8cfc332065927a03553a3b1f5531571cd4d5da119c6`;
- helper source SHA-256 `dfb564fbd644fae756808fee2afc1f43c35d0dde095e33ad9f4802569e80007a`;
- future-dated evidence rejection;
- authenticated authority/issuer + immutable record/version binding;
- distinct-issuer corroboration;
- repairable evidence acquisition/integrity failures;
- exact decision/effect/evidence-root binding;
- finality-gated and idempotent decision application;
- deadline recovery and late-callback guards;
- direct-origin claim guard;
- **117** Direct Runtime tests;
- **454** non-runtime Python tests + **334** subtests;
- **27** frontend unit tests;
- **12** browser E2E tests;
- production frontend build and local security-header checks.

## Current live evidence

The previously published `e9858985495111cf2f21db6dc847c7f75b79c0da` release has
an exact-source finalized coordinator deployment at
`0x7C1e450333D97CD4E02F48c3424BF10112697A60`. Historical v0.7 missions 008/009
remain historical live COMMIT/ABORT behavior proof.

The current hardening source is deployed and byte-verified on Studio Next at
`0xEE21cCFF8f3755487f774BFd5Da9Ff51D5688581` with deployment transaction
`0xc0e377d7a76893c253d61fcce42a320c6f5f41e5afad013a59dcbd279a998a50`.
The deployment is `FINALIZED`, `FINISHED_WITH_RETURN`, and `MAJORITY_AGREE`
with outer rotations `3` and fee-distribution rotations `[3]`. Fresh
current-source COMMIT and ABORT missions each reached the expected terminal
state through one finalized self-callback and one finalized claim. Full hashes
are recorded in
[`LIVE_STUDIO_NEXT_LIFECYCLE_2026-09-16.md`](./LIVE_STUDIO_NEXT_LIFECYCLE_2026-09-16.md).

## Still bounded or separately certifiable

- current-source recovery/stale-callback proof on the hosted network (the
  state-machine and runtime suites cover these cases locally);
- an explicit live proof of downstream external GEN delivery/reconciliation;
- the documented external GEN delivery/retry/reconciliation limitation.

## Not claimed

COMMIT does not claim arbitrary natural-language AI interpretation in the
current reference policy, rollback of external systems, proof that distinct
addresses are independent organizations, or generic downstream EVM delivery
reconciliation.

Its atomic guarantee is intentionally narrower: protocol-held settlement rights
are allocated only by the declared finalized COMMIT/ABORT state machine.
