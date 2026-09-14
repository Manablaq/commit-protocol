# Submission boundaries

COMMIT is deliberately explicit about what the Agent Tank proof does and does not establish.

## Proven

- source-matched live Studio Dev deployment for revision `0.7.0-reviewable-manifest`;
- finalized COMMIT and ABORT paths on that deployment;
- exact mission/effect/evidence root reconstruction;
- finality-gated allocation;
- one-time claim/refund entitlement consumption;
- locally certified current source with exact evidence authority, freshness, corroboration, repair, recovery, and consequence binding;
- deterministic and Direct Runtime coverage for callback races and replay guards.

## Not claimed

- synchronous rollback of arbitrary external systems;
- source identity between the current repository checkpoint and the historical Studio Dev v0.7 address;
- authenticated proof that every external native-value child was delivered to its downstream recipient;
- production-grade retry/reconciliation for a failed downstream transfer;
- production custody readiness outside the tested Agent Tank scope.

These boundaries are intentional. COMMIT's core guarantee is about when protocol-held settlement rights may be allocated and consumed, not about making the rest of the internet transactional.
