# Production release record — 2026-09-16

This record identifies the production application currently served by the
canonical Vercel alias and the exact Studio Next coordinator it targets.

## Release identity

- Repository: `https://github.com/Manablaq/commit-protocol`
- Deployed application source commit: `d25e689b0d5c681755751da257700f0d3f7974d1`
- Deployed application source tree: `5553aa58ab006c85000c5a2b106988da2b61f002`
- Public application: `https://commit-protocol.vercel.app`
- Vercel project: `mr-albert-s-projects/commitprotocol-genlayer`
- Vercel production deployment: `dpl_Cwh63QydtcGyVD9MeZ7jrSo3A1QE`
- Deployment state: `READY` / `PRODUCTION`

The source commit and tree above are the exact release built and published by
the recorded Vercel deployment. The deployment includes the narrow-viewport
overflow fix certified by the browser E2E gate.

## Served contract binding

- Network: **GenLayer Studio Next**
- RPC: `https://studio-next.genlayer.com/api`
- Chain ID: `61997` (`0xf22d`)
- Coordinator: `0xEE21cCFF8f3755487f774BFd5Da9Ff51D5688581`
- Deployment transaction:
  `0xc0e377d7a76893c253d61fcce42a320c6f5f41e5afad013a59dcbd279a998a50`

The served production bundle contains the certified coordinator address and
does not contain the superseded `0x7C1e450...` deployment anchor. The active
wallet path uses the explicit Studio Next chain configuration and does not call
the obsolete `client.connect("studioDevnet")` path. The SDK package still
contains its own historical chain metadata; that inert library metadata is not
used as the application's network target.

## Production verification

Read-only checks against `https://commit-protocol.vercel.app` passed:

- `/`: HTTP 200
- `/app`: HTTP 200
- `/verify`: HTTP 200
- `/api/v1/health`: HTTP 200 with durable-state health schema
- valid `/api/v1/index` request for chain `61997` and the certified coordinator:
  HTTP 200 with typed `found: false` response for an empty index
- valid transaction lookup for a zero hash: HTTP 200 with typed `found: false`
- baseline security headers: `nosniff`, `DENY`, strict referrer policy,
  restricted camera/microphone/geolocation, and HSTS
- browser rendering of `/app` and `/verify`: passed with no console errors
- verification-center “Read index” action: passed without a page reload or
  client-side error
- deployed JavaScript bundle contains the certified coordinator anchor and the
  strict `EXTERNAL MESSAGE OBSERVATION` claim surface
- GitHub Actions `Verification` run `35140950751` for the repository release:
  completed successfully across Python, Direct Runtime, and frontend jobs

The verification API remains read-only. It does not reconstruct chain truth or
claim that an external GEN transfer was delivered after native-value dispatch.

## Remaining bounded protocol limitation

COMMIT proves allocation and one-time consumption of protocol-held settlement
rights. Studio Next does not currently provide a contract-usable, authenticated
delivery receipt plus safe retry/reconciliation primitive for arbitrary
downstream GEN transfers. Therefore the application does not claim
downstream delivery, automatic retry, or rollback beyond the documented
settlement boundary.

The exact coordinator deployment and fresh COMMIT/ABORT lifecycle evidence are
recorded in
[`LIVE_STUDIO_NEXT_LIFECYCLE_2026-09-16.md`](./LIVE_STUDIO_NEXT_LIFECYCLE_2026-09-16.md).
