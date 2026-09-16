# Local verification record

Updated: 2026-09-16.

This record covers the local verification gates for the reviewer-hardening
candidate. The certified source-bound release is now on `main` and has a
separate finalized Studio Next deployment record.

## Candidate source identity

Base GitHub main before candidate publication:

`092d1424ed809540a983a594e6941e562ca034df`

- coordinator: `contracts/commit.py`
- coordinator SHA-256: `e235731ac223ee136b06b8cfc332065927a03553a3b1f5531571cd4d5da119c6`
- coordinator bytes: `19873`
- helper: `contracts/commit_helper.py`
- helper SHA-256: `dfb564fbd644fae756808fee2afc1f43c35d0dde095e33ad9f4802569e80007a`
- helper bytes: `9428`

The candidate was intentionally source-different from the previously deployed
`e9858985495111cf2f21db6dc847c7f75b79c0da` coordinator. The replacement
deployment and its exact byte match are recorded in
[`LIVE_STUDIO_NEXT_LIFECYCLE_2026-09-16.md`](./LIVE_STUDIO_NEXT_LIFECYCLE_2026-09-16.md).

## Hardened behavior added

The candidate:

- rejects evidence whose `published_at` is later than the GenLayer transaction
  clock;
- exposes the constructor-bound helper address through `protocol_info`;
- requires the public claim path to be initiated directly by the beneficiary
  transaction origin;
- uses hosted-Studio-compatible transaction reads in the verification backend;
- filters Vercel route-capture metadata without weakening public query-shape
  validation;
- makes the health endpoint verify durable state readability;
- aligns the browser SDK dependency with `genlayer-js==2.0.0-rc.1`;
- adds baseline browser security headers.

## Static contract certification

Both coordinator and helper pass:

- `genvm-lint check`
- `genvm-lint typecheck`

The helper remains stateless/view-only and byte-identical to the previously
certified helper source.

## Python/runtime certification

Final hardening results:

- Direct Runtime: **117 passed**
- non-runtime Python regression: **454 passed + 334 subtests**
- official GenVM Manager `v0.6.0-rc5` archive SHA-256:
  `bd30580f911338d5533460eca8ed714dec371de5803c04e41dbb96430aea7b6e`

The Direct Runtime includes explicit positive regression coverage for both the
future-publication rejection and indirect-origin claim rejection.

## Frontend certification

- TypeScript: pass
- ESLint: pass
- Vitest: **46 passed**
- production Next.js build: pass
- Playwright browser E2E: **12 passed**
- local production `/app` and `/verify`: HTTP 200
- local production baseline security headers: pass

## Network status

This file records local gates only; it does not itself constitute a chain
transaction, wallet signature, remote Git push, or Vercel deployment record.
The current source-bound Studio Next deployment, exact source match, and fresh
COMMIT/ABORT lifecycle evidence are recorded separately in
[`LIVE_STUDIO_NEXT_LIFECYCLE_2026-09-16.md`](./LIVE_STUDIO_NEXT_LIFECYCLE_2026-09-16.md).
The hosted Vercel release, served contract anchor, route-capture handling, and
production smoke checks are recorded in
[`PRODUCTION_RELEASE_2026-09-16.md`](./PRODUCTION_RELEASE_2026-09-16.md).
