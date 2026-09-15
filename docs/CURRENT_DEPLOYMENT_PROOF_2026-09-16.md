# Current deployment proof — 2026-09-16

This document records the reviewer-facing deployment identity for the current
COMMIT release. It supersedes the unresolved deployment status recorded in
[`STUDIO_NEXT_CHECKPOINT_2026-09-15.md`](./STUDIO_NEXT_CHECKPOINT_2026-09-15.md)
without deleting that historical diagnostic record.

## Release identity

- Repository release commit: `e9858985495111cf2f21db6dc847c7f75b79c0da`
- Release tree: `3627b57a0baaebda07b15da76cb8b594ee4a18f9`
- Coordinator source: `contracts/commit.py`
- Coordinator source SHA-256: `be0ef1686314354ac1b87ccd50ab42f0c933c312a4980c0e5479f2d3037e4e58`
- Coordinator source bytes: `19670`
- Helper source SHA-256: `dfb564fbd644fae756808fee2afc1f43c35d0dde095e33ad9f4802569e80007a`

## Canonical hosted Studio network

- Network label: **GenLayer Studio development preview**
- Canonical RPC: `https://studio-dev.genlayer.com/api`
- Chain ID: `61997` / `0xf22d`
- `https://studio-next.genlayer.com/api` resolves to the same chain and returned
  the same transaction and deployed code for the checks below. It is treated
  here as an alias comparison, not as a separate SDK network or a second
  deployment requirement.

## Current coordinator deployment

- Contract: `0x7C1e450333D97CD4E02F48c3424BF10112697A60`
- Deployment transaction: `0x496654c019c07ffeed87fb8021e482d18f5da125c2388538d5ea88d81a6a7640`
- Stored transaction status: `FINALIZED`
- Execution result: `FINISHED_WITH_RETURN`
- Deployed code bytes: `19670`
- Deployed code SHA-256: `be0ef1686314354ac1b87ccd50ab42f0c933c312a4980c0e5479f2d3037e4e58`
- Exact source match: **yes**

The deployment was re-read independently through supported hosted-Studio RPC
methods:

- `eth_getTransactionByHash`
- `gen_getTransactionStatus`
- `gen_getContractCode`

The canonical Studio endpoint and the Studio-next alias both returned:

- chain ID `0xf22d`;
- deployment transaction `0x496654c019c07ffeed87fb8021e482d18f5da125c2388538d5ea88d81a6a7640`;
- status `FINALIZED`;
- execution `FINISHED_WITH_RETURN`;
- target `0x7C1e450333D97CD4E02F48c3424BF10112697A60`;
- deployed source SHA-256 `be0ef1686314354ac1b87ccd50ab42f0c933c312a4980c0e5479f2d3037e4e58`;
- deployed source byte count `19670`.

The read-only verification submitted no transaction and requested no wallet
signature.

Local F18 evidence packet index SHA-256:

`ec6ff2dda8fec5338d353a3408ca8f7bb674f13f8ea7b24c7ecf6193003ba4b3`

## Public application release

- Public URL: https://commitprotocol-genlayer.vercel.app
- GitHub main: `e9858985495111cf2f21db6dc847c7f75b79c0da`
- Vercel production deployment ID: `dpl_6x9XzgAxPsRX8jXr7d6KonmEmL6S`
- Production release tree: `3627b57a0baaebda07b15da76cb8b594ee4a18f9`
- Final public alias certification: **passed**
- Public `/`, `/app`, `/verify`, and `/api/v1/health`: **HTTP 200**
- Public application/verification/health bodies matched the promoted production
  clone during final publication certification.

Local F17 publication evidence packet index SHA-256:

`8888ee93b3751854214758a453d97c17b73d6cc52b9163d40235c7316a75a2c4`

## Scope of proof

This document proves the identity, finality, execution result, and exact source
bytes of the **current coordinator deployment**.

It does not rewrite history. The earlier Studio diagnostic in
`STUDIO_NEXT_CHECKPOINT_2026-09-15.md` genuinely failed before a transaction
was submitted. That checkpoint is retained as historical evidence and is now
superseded by the successful deployment above.

The older v0.7 Studio Dev deployment in
[`DEPLOYMENT_LOG_STUDIO_DEV.md`](./DEPLOYMENT_LOG_STUDIO_DEV.md) remains the
recorded live end-to-end behavior proof for both the COMMIT and ABORT lifecycle
branches. Those historical branch proofs are not represented as executions of
the newer release commit.
