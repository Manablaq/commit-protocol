# Agent Tank submission proof map

This document is the shortest path for an Agent Tank judge or reviewer to understand what COMMIT is, what is live, and what is locally certified.

## Project

**COMMIT — semantic atomicity for autonomous economic workflows**

COMMIT freezes a mission's economic intent, evidence identities, and proposed effects before semantic adjudication. GenLayer validators evaluate the external evidence. Only a finalized decision can allocate escrowed COMMIT/ABORT settlement rights.

## Live GenLayer proof

- Network: **Studio Dev**
- Chain ID: `61997`
- Source-matched contract: `0x10c708517b4465596E2dc40De92B30A610Cb7a10`
- Source revision: `0.7.0-reviewable-manifest`
- Deployment transaction: `0x03071d2f8353c993a6a8aae38c1086e025df712f320090fd036ace2ef218ccab`
- Deployment result: `FINALIZED`, `FINISHED_WITH_RETURN`
- Source SHA-256: `4dd61b7e7a5acbdc254f7a63419fe7b4a2674909d49fa07e0d0b051fd74eb36f`

Full evidence: [`DEPLOYMENT_LOG_STUDIO_DEV.md`](./DEPLOYMENT_LOG_STUDIO_DEV.md).

## End-to-end outcome proofs

### COMMIT branch — mission 008

Mission 008 proves the successful semantic-settlement path:

- mission terms and roots were frozen;
- two bound evidence records were evaluated;
- the decision was `COMMIT`;
- the finalized callback applied allocation once;
- the claim consumed the internal entitlement once before external dispatch.

### ABORT branch — mission 009

Mission 009 proves the negative/refund path:

- one bound record was ineligible under the all-records-and-effects policy;
- the decision was `ABORT`;
- the finalized callback allocated the refund path once;
- the refund entitlement was consumed once.

Both paths use the same deployed v0.7 bytecode.

## Current repository source

The current certified source checkpoint is:

- Commit: `c152ec75d935a4cb5cf37e2f31aaae89c1bdc525`
- Coordinator SHA-256: `e88d1d78ee8f2d373124bbfbc3f0c8d946385a3250fc028f5956fd74762f8c69`
- Helper SHA-256: `0120b74e0988f2444c3cc824bd40633c472348da9e1d3fd851c4d7380ffbe632`

The current source preserves the 41-method coordinator API while separating deterministic helper work into a stateless view-only contract. The coordinator remains the sole custody, mission-state, nondeterministic-evaluation, finality, allocation, and native-transfer boundary.

This newer source is not represented as the same source deployed at the Studio Dev v0.7 address. The live v0.7 deployment is behavior evidence; the newer checkpoint is the current locally certified implementation.

## Certification snapshot — 2026-09-14

The current source checkpoint passed:

- GenVM typecheck/lint/validation for both contracts;
- 70 semantic regression tests;
- 113 Direct Runtime tests;
- 433 repository tests plus 334 subtests;
- exact public ABI parity;
- stateless/view-only helper guards;
- read-only deployment-envelope qualification.

No later network deployment is required to understand or reproduce the repository's current verification record.

## Judge-facing technical claims

COMMIT claims:

- exact evidence/mission/effect binding;
- explicit authority and issuer trust;
- freshness, expiry, stable record identity, and version binding;
- independent corroboration;
- repairable acquisition/integrity failures;
- exact validator agreement on consequential values;
- finality-gated allocation;
- deadline recovery;
- one-time claim consumption.

COMMIT does **not** claim:

- rollback of arbitrary external systems;
- that the current repository source is identical to the historical Studio Dev v0.7 deployment;
- authenticated proof of downstream external GEN delivery after dispatch;
- production custody readiness beyond the explicitly tested boundary.
