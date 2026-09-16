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

## Repository deployment tooling

The repository contains two separate commands so submission and finality cannot
be conflated:

```text
node scripts/deploy_studio_next.mjs
node scripts/finalize_studio_next.mjs
```

`deploy:studio-next` is read-only by default. It resolves the unlocked worker
through the GenLayer CLI keychain bridge, binds the exact coordinator source and
helper, reads the live Studio Next fee policy, recomputes the fee deposit with
`rotations: [3]`, and prints a preflight summary. Write mode requires both
`COMMIT_DEPLOY_PREFLIGHT_ONLY=0` and the exact explicit confirmation token
`COMMIT_DEPLOY_CONFIRM=ONE_STUDIO_NEXT_DEPLOYMENT`, plus a new marker path in
`COMMIT_DEPLOY_MARKER`. The marker is created before submission and prevents an
automatic retry after an ambiguous RPC response.

`finalize:studio-next` is run later with the returned transaction hash and an
evidence directory. It waits for finality, checks successful execution, reads
the exact deployed bytes, verifies `protocol_info()`, and rejects any receipt
whose recorded outer or fee-distribution rotation value is not `3`.

## Previously published deployment

The public application still points at the previously certified coordinator
until the hardening candidate is replaced and re-certified. That historical
release was recorded through the SDK-compatible Studio Dev endpoint:

- deployed application release: `e9858985495111cf2f21db6dc847c7f75b79c0da`
- deployed release tree: `3627b57a0baaebda07b15da76cb8b594ee4a18f9`
- coordinator: `0x7C1e450333D97CD4E02F48c3424BF10112697A60`
- deployment transaction: `0x496654c019c07ffeed87fb8021e482d18f5da125c2388538d5ea88d81a6a7640`
- deployed coordinator SHA-256: `be0ef1686314354ac1b87ccd50ab42f0c933c312a4980c0e5479f2d3037e4e58`
- stored result: `FINALIZED` + `FINISHED_WITH_RETURN`

That proof remains historical evidence for the previously published
application release. It is not the current source-bound coordinator.

## Current source-bound deployment

Repository HEAD: `e402af3978a51012223b035652b85fc77001485b`

Base GitHub main before publication:

`092d1424ed809540a983a594e6941e562ca034df`

Candidate source identities:

- coordinator SHA-256: `e235731ac223ee136b06b8cfc332065927a03553a3b1f5531571cd4d5da119c6`
- coordinator bytes: `19873`
- helper SHA-256: `dfb564fbd644fae756808fee2afc1f43c35d0dde095e33ad9f4802569e80007a`
- helper bytes: `9428`

The helper source has not changed in this hardening cycle. The finalized
coordinator deployment is bound to helper
`0x53405950e587Ca4F6232b4596f0992ea5aaD8Ae4`.

## Verified local runtime

The candidate is certified against the official GenVM Manager `v0.6.0-rc5`
universal release archive:

`bd30580f911338d5533460eca8ed714dec371de5803c04e41dbb96430aea7b6e`

The verified archive contains both the current `py-genlayer` runner and the
historical legacy runner required by the Direct Runtime suite.

## Current certification state

The hardening candidate has passed the local deterministic/runtime/frontend
gates and the corrected Studio Next deployment is certified by the finalized
three-rotation envelope, exact source match, protocol readback, and fresh
COMMIT/ABORT lifecycle evidence. See
[`LIVE_STUDIO_NEXT_LIFECYCLE_2026-09-16.md`](./LIVE_STUDIO_NEXT_LIFECYCLE_2026-09-16.md).
