# Submission environment

This file distinguishes the previously published release from the final
reviewer-hardening candidate and records the network identity required for the
submission.

## Canonical hackathon submission environment

The accepted current-source deployment target is **GenLayer Studio Next**:

- Submission RPC: `https://studio-next.genlayer.com/api`
- Chain ID: `61997` / `0xf22d`
- Explorer: `https://explorer-studio-dev.genlayer.com/`

The `genlayer-js` chain definition is named `studioDevnet` and uses
`https://studio-dev.genlayer.com/api` as its SDK endpoint. Read-only checks show
that endpoint and the Studio Next submission endpoint currently expose the same
chain ID. The SDK endpoint is therefore a compatibility alias, not the
submission target. A deployment is certified only when it is submitted through
the Studio Next endpoint and its transaction records chain ID `61997` plus the
required non-zero rotation budget.

## Deployment-envelope invariant

The deployment request must bind both values explicitly:

- outer `consensusMaxRotations`: `3`;
- fee distribution `rotations`: `[3]`.

The fee distribution is not allowed to retain the SDK default `[0]`. The fee
deposit must be re-measured against the live Studio Next policy after the
distribution is set. The deployment preflight must fail closed unless the
serialized request and finalized transaction prove those values.

## Currently published deployment

The public application still points at the previously certified coordinator
until the hardening candidate is replaced and re-certified. That historical
release was recorded through the SDK-compatible Studio Dev endpoint:

- deployed application release: `e9858985495111cf2f21db6dc847c7f75b79c0da`
- deployed release tree: `3627b57a0baaebda07b15da76cb8b594ee4a18f9`
- coordinator: `0x7C1e450333D97CD4E02F48c3424BF10112697A60`
- deployment transaction: `0x496654c019c07ffeed87fb8021e482d18f5da125c2388538d5ea88d81a6a7640`
- deployed coordinator SHA-256: `be0ef1686314354ac1b87ccd50ab42f0c933c312a4980c0e5479f2d3037e4e58`
- stored result: `FINALIZED` + `FINISHED_WITH_RETURN`

That proof remains historical/current-production evidence. It is **not** a
claim that the new hardening candidate below is submission-certified.

## Final hardening candidate

Local branch: `fix/final-reviewer-blockers-r1`

Base GitHub main before publication:

`092d1424ed809540a983a594e6941e562ca034df`

Candidate source identities:

- coordinator SHA-256: `e235731ac223ee136b06b8cfc332065927a03553a3b1f5531571cd4d5da119c6`
- coordinator bytes: `19873`
- helper SHA-256: `dfb564fbd644fae756808fee2afc1f43c35d0dde095e33ad9f4802569e80007a`
- helper bytes: `9428`

The helper source has not changed in this hardening cycle. Before the final
coordinator deployment, the existing helper binding and exact deployed helper
bytes must be proved read-only; the helper is redeployed only if that proof
fails.

## Verified local runtime

The candidate is certified against the official GenVM Manager `v0.6.0-rc5`
universal release archive:

`bd30580f911338d5533460eca8ed714dec371de5803c04e41dbb96430aea7b6e`

The verified archive contains both the current `py-genlayer` runner and the
historical legacy runner required by the Direct Runtime suite.

## Current transition state

The hardening candidate has passed local deterministic/runtime/frontend gates
and has an exact-source Studio Next deployment, but that deployment is **not
certified** because the submitted envelope recorded zero rotations. A fresh
replacement coordinator deployment is required with the corrected `[3]` fee
distribution and outer rotation budget. Final Agent Tank documentation must be
updated again with the replacement address, transaction, finality result, exact
source proof, live COMMIT/ABORT outcomes, and preview/production certification.
