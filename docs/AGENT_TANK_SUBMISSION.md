# Agent Tank submission proof map

This is the shortest reviewer path through the final COMMIT release.

## Project

**COMMIT — semantic atomicity for autonomous economic workflows**

COMMIT freezes a mission's economic intent, evidence identities, and prepared
effects before semantic adjudication. GenLayer validators evaluate the bounded
external evidence. Only a finalized decision can allocate the escrowed
COMMIT/ABORT settlement rights.

## Live application

- Public app: `https://commitprotocol-genlayer.vercel.app`
- GitHub: `https://github.com/Manablaq/commit-protocol`
- Final release commit:
  `e9858985495111cf2f21db6dc847c7f75b79c0da`
- Release tree:
  `3627b57a0baaebda07b15da76cb8b594ee4a18f9`
- Vercel production deployment:
  `dpl_6x9XzgAxPsRX8jXr7d6KonmEmL6S`

## Current exact-source GenLayer deployment

- Network: **GenLayer Studio development preview**
- Canonical RPC: `https://studio-dev.genlayer.com/api`
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

The final read-only deployment gate re-read the transaction, stored final
status, and deployed contract code through supported hosted-Studio RPC methods.
The Studio-next hostname returned the same chain, transaction, status,
execution result, target, and source bytes and is treated as an alias comparison
rather than a separate deployment requirement.

Full proof:
[`CURRENT_DEPLOYMENT_PROOF_2026-09-16.md`](./CURRENT_DEPLOYMENT_PROOF_2026-09-16.md).

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

## Final verification snapshot

The release has the following final certification record:

- coordinator source SHA-256:
  `be0ef1686314354ac1b87ccd50ab42f0c933c312a4980c0e5479f2d3037e4e58`;
- helper source SHA-256:
  `dfb564fbd644fae756808fee2afc1f43c35d0dde095e33ad9f4802569e80007a`;
- Python regression: **450 passed + 334 subtests**;
- frontend Vitest: **27 passed**;
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
- finality-gated allocation;
- deadline recovery for locked value;
- idempotent decision application;
- consume-before-dispatch settlement rights;
- bounded evidence, text, graph, and remote-body inputs.

COMMIT does **not** claim:

- rollback of arbitrary external systems;
- that the historical v0.7 COMMIT/ABORT executions were performed by the newer
  release commit;
- authenticated proof of downstream external GEN delivery after dispatch;
- production custody readiness beyond the explicitly tested boundary.

## Reviewer path

1. Read this file.
2. Verify the exact current deployment in
   [`CURRENT_DEPLOYMENT_PROOF_2026-09-16.md`](./CURRENT_DEPLOYMENT_PROOF_2026-09-16.md).
3. Inspect the historical COMMIT/ABORT lifecycle evidence in
   [`DEPLOYMENT_LOG_STUDIO_DEV.md`](./DEPLOYMENT_LOG_STUDIO_DEV.md).
4. Review the security boundary in
   [`THREAT_MODEL.md`](./THREAT_MODEL.md) and
   [`SEMANTIC_ATOMICITY.md`](./SEMANTIC_ATOMICITY.md).
5. Open the live application and its `/verify` read surface.
