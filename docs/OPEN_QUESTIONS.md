# Submission boundaries

COMMIT is explicit about what is already proven and what remains to be
certified before Agent Tank submission.

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

## Existing live evidence

The currently published `e9858985495111cf2f21db6dc847c7f75b79c0da` release has an exact-source finalized
coordinator deployment at `0x7C1e450333D97CD4E02F48c3424BF10112697A60`. Historical v0.7 missions
008/009 remain the existing live COMMIT/ABORT behavior proof.

The new `e235731ac223ee136b06b8cfc332065927a03553a3b1f5531571cd4d5da119c6`
hardening candidate has since been deployed and byte-verified on Studio Next at
`0x597641c88a3644f2C8c5c0baD9F1072710a82E85`, but that deployment used a
zero-rotation envelope and is not a certified submission deployment. No
current-source lifecycle execution is represented yet.

## Still required before submission

- exact helper deployed-code/constructor-binding proof;
- target-network candidate fee/message-allocation measurement;
- fresh exact-source coordinator deployment;
- current-source live COMMIT and ABORT lifecycle proof;
- current-source recovery/stale-callback proof;
- EOA claim/refund proof;
- isolated Vercel preview certification of the repaired `/verify` data path;
- durable reviewer-inspectable evidence artifacts;
- final production promotion and documentation update.

## Not claimed

COMMIT does not claim arbitrary natural-language AI interpretation in the
current reference policy, rollback of external systems, proof that distinct
addresses are independent organizations, or generic downstream EVM delivery
reconciliation.

Its atomic guarantee is intentionally narrower: protocol-held settlement rights
are allocated only by the declared finalized COMMIT/ABORT state machine.
