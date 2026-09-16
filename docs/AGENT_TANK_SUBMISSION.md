# Agent Tank submission proof map

> **Current certification:** the reviewer-hardening coordinator source is
> deployed and lifecycle-verified on Studio Next. The exact deployment,
> source-match, COMMIT/ABORT, callback, and claim evidence is in
> [`LIVE_STUDIO_NEXT_LIFECYCLE_2026-09-16.md`](./LIVE_STUDIO_NEXT_LIFECYCLE_2026-09-16.md).

This is the shortest reviewer path through the final COMMIT release.

## Project

**COMMIT — Onchain Justice for autonomous commerce**

COMMIT freezes a mission's economic intent, evidence identities, and prepared
effects before semantic adjudication. Its Case Room makes the complete path
visible: Agreement → Escrow → Evidence → Verdict → Appeal → Finality →
Settlement. GenLayer validators evaluate the bounded external evidence, and
only a finalized decision can allocate the escrowed COMMIT/ABORT settlement
rights. The native appeal surface reads the exact evaluation transaction and
uses the SDK's authoritative eligibility, charge, and appeal operations.

## Live application

- Public app: `https://commit-protocol.vercel.app`
- GitHub: `https://github.com/Manablaq/commit-protocol`
- Production source commit:
  `53fb52f2d8d7c5a3636810501b740d859d5a2c14`
- Production source tree:
  `91c5f458dd77f7d38f0c8107f00eb15a74c3ce37`
- Vercel production deployment:
  `dpl_BvXSZgubPSzs3Z9cyck6eY5dzvDt`
- Served coordinator:
  `0xEE21cCFF8f3755487f774BFd5Da9Ff51D5688581`
- GitHub Actions `Verification` run: `35142284628` — all jobs passed

Production smoke checks and the exact served-bundle binding are recorded in
[`PRODUCTION_RELEASE_2026-09-16.md`](./PRODUCTION_RELEASE_2026-09-16.md).

## Current source-bound Studio Next deployment

- Network: **GenLayer Studio Next**
- RPC: `https://studio-next.genlayer.com/api`
- Chain ID: `61997`
- Coordinator:
  `0xEE21cCFF8f3755487f774BFd5Da9Ff51D5688581`
- Helper: `0x53405950e587Ca4F6232b4596f0992ea5aaD8Ae4`
- Deployment transaction:
  `0xc0e377d7a76893c253d61fcce42a320c6f5f41e5afad013a59dcbd279a998a50`
- Deployment result: `FINALIZED`, `FINISHED_WITH_RETURN`, `MAJORITY_AGREE`
- Source SHA-256:
  `e235731ac223ee136b06b8cfc332065927a03553a3b1f5531571cd4d5da119c6`
- Deployed source bytes: `19873`
- Outer and fee-distribution rotations: `3` and `[3]`

Current lifecycle proof:
[`LIVE_STUDIO_NEXT_LIFECYCLE_2026-09-16.md`](./LIVE_STUDIO_NEXT_LIFECYCLE_2026-09-16.md).

## Historical published GenLayer deployment

- Network: **GenLayer Studio development preview (historical release)**
- Recorded RPC: `https://studio-dev.genlayer.com/api`
- Chain ID: `61997` / `0xf22d`
- Coordinator:
  `0x7C1e450333D97CD4E02F48c3424BF10112697A60`
- Deployment transaction:
  `0x496654c019c07ffeed87fb8021e482d18f5da125c2388538d5ea88d81a6a7640`
- Stored status: `FINALIZED`
- Execution: `FINISHED_WITH_RETURN`
- Coordinator source SHA-256:
  `be0ef1686314354ac1b87ccd50ab42f0c933c312a4980c0e5479f2d3037e4e58`
- Deployed source bytes: `19670`
- Exact source match: **confirmed**

This is historical proof for the previously published release. The current
source-bound deployment is recorded above.

## Current submission target

The current-source deployment targets **Studio Next**:

- RPC: `https://studio-next.genlayer.com/api`
- Chain ID: `61997` / `0xf22d`
- Explorer: `https://explorer-studio-dev.genlayer.com/`
- Required outer rotation budget: `3`
- Required fee-distribution rotations: `[3]`

The browser integration builds an explicit Studio Next chain object from neutral
SDK Studio metadata. It does not select the historical `studioDevnet` endpoint,
and the finalized deployment plus three-rotation envelope are certified in the
current lifecycle proof.

Full proof:
[`LIVE_STUDIO_NEXT_LIFECYCLE_2026-09-16.md`](./LIVE_STUDIO_NEXT_LIFECYCLE_2026-09-16.md).

## Historical live outcome proofs

The earlier source-matched v0.7 Studio Dev deployment remains the live
end-to-end behavior proof for both semantic branches:

- Contract: `0x10c708517b4465596E2dc40De92B30A610Cb7a10`
- Deployment transaction:
  `0x03071d2f8353c993a6a8aae38c1086e025df712f320090fd036ace2ef218ccab`
- Result: `FINALIZED`, `FINISHED_WITH_RETURN`
- Source SHA-256:
  `4dd61b7e7a5acbdc254f7a63419fe7b4a2674909d49fa07e0d0b051fd74eb36f`

### COMMIT branch — mission 008

Mission 008 proves the successful settlement path:

- mission terms and roots were frozen;
- two bound evidence records were evaluated;
- the decision was `COMMIT`;
- the finalized callback allocated the prepared entitlement once;
- the claim consumed that entitlement once before external dispatch.

### ABORT branch — mission 009

Mission 009 proves the negative/refund path:

- one bound record was ineligible under the all-records-and-effects policy;
- the decision was `ABORT`;
- the finalized callback allocated the refund path once;
- the refund entitlement was consumed once.

These branch proofs are historical behavior evidence and are not represented as
executions of the newer release commit.

Full historical record:
[`DEPLOYMENT_LOG_STUDIO_DEV.md`](./DEPLOYMENT_LOG_STUDIO_DEV.md).

## Historical published-release verification snapshot

The earlier published release has the following historical certification record:

- coordinator source SHA-256:
  `be0ef1686314354ac1b87ccd50ab42f0c933c312a4980c0e5479f2d3037e4e58`;
- helper source SHA-256:
  `dfb564fbd644fae756808fee2afc1f43c35d0dde095e33ad9f4802569e80007a`;
- Python regression: **450 passed + 334 subtests**;
- frontend Vitest: **46 passed**;
- browser E2E: **12 passed**;
- public `/`, `/app`, `/verify`, `/api/v1/health`: **HTTP 200**;
- public production bodies matched the promoted production clone during final
  release certification;
- deployment transaction: **FINALIZED**;
- deployment execution: **FINISHED_WITH_RETURN**;
- current coordinator deployed bytes: **exact source match**.

## Judge-facing technical claims

COMMIT claims:

- explicit authority and issuer trust;
- immutable mission/evidence identity and version binding;
- freshness and expiry constraints;
- independent corroboration;
- exact evidence/mission/effect binding;
- repairable evidence acquisition and integrity failures;
- exact validator agreement on consequential values;
- native appeal lifecycle visibility and exact-charge appeal submission;
- finality-gated allocation;
- deadline recovery for locked value;
- idempotent decision application;
- consume-before-dispatch settlement rights;
- strict read-only observation of the exact triggered child message, including
  recipient/value binding and finalized execution result;
- bounded evidence, text, graph, and remote-body inputs.

COMMIT does **not** claim:

- rollback of arbitrary external systems;
- that the historical v0.7 COMMIT/ABORT executions were performed by the newer
  release commit;
- authenticated proof of downstream external GEN delivery after dispatch;
- production custody readiness beyond the explicitly tested boundary.

The live application does expose an operator observation path for a triggered
claim child transaction. It reports delivery only when the exact beneficiary,
amount, `FINALIZED` status, and `FINISHED_WITH_RETURN` result match. Missing,
ambiguous, pending, or mismatched child data remains unverified, and the
application does not retry automatically. This improves visibility without
overstating the current Studio Next delivery guarantee.

## Reviewer path

1. Read this file.
2. Verify the exact current deployment in
   [`LIVE_STUDIO_NEXT_LIFECYCLE_2026-09-16.md`](./LIVE_STUDIO_NEXT_LIFECYCLE_2026-09-16.md).
3. Inspect the historical published-release record in
   [`CURRENT_DEPLOYMENT_PROOF_2026-09-16.md`](./CURRENT_DEPLOYMENT_PROOF_2026-09-16.md)
   and the earlier branch evidence in [`DEPLOYMENT_LOG_STUDIO_DEV.md`](./DEPLOYMENT_LOG_STUDIO_DEV.md).
4. Review the security boundary in
   [`THREAT_MODEL.md`](./THREAT_MODEL.md) and
   [`SEMANTIC_ATOMICITY.md`](./SEMANTIC_ATOMICITY.md).
5. Open the live application and its `/verify` read surface.
