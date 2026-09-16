# Submission environment

This file distinguishes the currently published application/deployment from the
final reviewer-hardening candidate that is still being certified locally.

## Canonical hosted GenLayer environment

COMMIT uses the hosted **GenLayer Studio development preview** as its canonical
submission environment:

- RPC: `https://studio-dev.genlayer.com/api`
- Chain ID: `61997` / `0xf22d`
- Explorer: `https://explorer-studio-dev.genlayer.com/`

`https://studio-next.genlayer.com/api` has been observed to expose the same
chain, transaction state, and deployed code for the recorded deployment. COMMIT
treats it only as an alias comparison; it is not represented as a separate SDK
network or a second deployment requirement.

## Currently published deployment

The public application still points at the previously certified coordinator
until the hardening candidate is deployed and re-certified:

- deployed application release: `e9858985495111cf2f21db6dc847c7f75b79c0da`
- deployed release tree: `3627b57a0baaebda07b15da76cb8b594ee4a18f9`
- coordinator: `0x7C1e450333D97CD4E02F48c3424BF10112697A60`
- deployment transaction: `0x496654c019c07ffeed87fb8021e482d18f5da125c2388538d5ea88d81a6a7640`
- deployed coordinator SHA-256: `be0ef1686314354ac1b87ccd50ab42f0c933c312a4980c0e5479f2d3037e4e58`
- stored result: `FINALIZED` + `FINISHED_WITH_RETURN`

That proof remains historical/current-production evidence. It is **not** a
claim that the new hardening candidate below is already deployed.

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

The hardening candidate has passed local deterministic/runtime/frontend gates,
but it has **not yet** been pushed, preview-deployed, or submitted on-chain.
A new coordinator deployment is required because the coordinator source bytes
changed. Final Agent Tank documentation must be updated again with that new
deployment address, transaction, finality result, exact source proof, live
COMMIT/ABORT outcomes, and preview/production certification.
