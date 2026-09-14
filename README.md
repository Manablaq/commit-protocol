# COMMIT

**Semantic atomicity for autonomous economic workflows.**

COMMIT is an Agent Tank 2026 project built on GenLayer. It lets autonomous participants agree on a mission, freeze the exact economic intent and evidence inputs, ask GenLayer validators to evaluate the outcome, and release escrowed settlement rights only after the decision reaches the required finality.

> Databases made data atomic. Blockchains made code atomic. COMMIT makes autonomous intentions atomic.

## The problem

Agentic workflows increasingly cross APIs, suppliers, evidence sources, and payment boundaries. A single transaction cannot make all of those external systems atomic, and an AI decision should not be allowed to move money unless the consequential facts are exactly bound to the decision.

COMMIT narrows that problem to an enforceable guarantee:

> For assets escrowed by COMMIT, settlement entitlements are allocated only after a finalized GenLayer decision over the mission's frozen intent, evidence, and prepared effects. Otherwise the mission follows its declared abort or recovery path.

COMMIT does **not** claim to roll back arbitrary external systems.

## How it works

1. A principal creates a mission with an objective, policy, budget, preparation deadline, recovery deadline, and refund beneficiary.
2. Authorized suppliers prepare bounded economic effects.
3. Evidence is registered against explicit authority, issuer, record, mission, version, freshness, and expiry constraints.
4. Sealing freezes the mission's intent, effect root, and evidence root.
5. GenLayer validators independently fetch the bounded evidence and agree on the exact consequential result.
6. A finalized self-message applies `COMMIT` or `ABORT` exactly once.
7. Claimable entitlements are consumed before native-value dispatch so the same right cannot be spent twice.

## Why GenLayer

COMMIT needs consensus over facts that ordinary deterministic contracts cannot resolve by themselves. GenLayer provides the validator execution model used to fetch and evaluate external evidence while COMMIT keeps the economic consequence deterministic, bounded, and reviewable.

## Agent Tank proof

### Live Studio Dev proof

The source-matched Studio Dev proof deployment is:

- Contract: `0x10c708517b4465596E2dc40De92B30A610Cb7a10`
- Network: GenLayer Studio Dev
- Chain ID: `61997`
- Revision: `0.7.0-reviewable-manifest`
- Deployment execution: `FINALIZED`, `FINISHED_WITH_RETURN`

The live record includes both policy outcomes on the same deployed bytecode:

- **Mission 008 — COMMIT:** two bound evidence records were accepted, the finalized callback allocated the prepared entitlement, and the claim consumed that entitlement exactly once.
- **Mission 009 — ABORT:** one evidence record was ineligible, the finalized callback allocated the refund path, and the refund entitlement was consumed exactly once.

See [`docs/DEPLOYMENT_LOG_STUDIO_DEV.md`](./docs/DEPLOYMENT_LOG_STUDIO_DEV.md).

### Latest certified source checkpoint

The repository's newer certified source checkpoint is commit:

`c152ec75d935a4cb5cf37e2f31aaae89c1bdc525`

It keeps the coordinator as the sole custody/state boundary and moves deterministic parsing/root helpers into the stateless `CommitHelper`.

Certification completed on 2026-09-14:

- public coordinator ABI: **41 methods, parity preserved**
- semantic regression file: **70 passed**
- Direct Runtime suite: **113 passed**
- repository regression suite: **433 passed + 334 subtests**
- GenVM lint/typecheck/validation: **passed** for coordinator and helper
- exact deployment-envelope read-only checks: **passed**

The latest repository source is **not claimed to be source-identical to the historical Studio Dev v0.7 deployment**. The Studio Dev deployment is the live behavior proof; `c152ec75...` is the later certified source checkpoint.

## Security properties

COMMIT is designed around the failure modes that matter when AI consensus can move economic state:

- authenticated evidence authority and issuer binding;
- immutable mission/evidence identity and version binding;
- freshness and expiry constraints;
- independent corroboration requirements;
- exact consensus-to-consequence binding;
- repairable evidence acquisition/integrity failures;
- recovery deadlines for locked value;
- finality-gated allocation;
- idempotent decision application;
- consume-before-dispatch claims;
- bounded evidence, text, graph, and remote-body inputs.

## Repository map

- [`contracts/commit.py`](./contracts/commit.py) — economic/state coordinator
- [`contracts/commit_helper.py`](./contracts/commit_helper.py) — stateless deterministic helper
- [`docs/AGENT_TANK_SUBMISSION.md`](./docs/AGENT_TANK_SUBMISSION.md) — submission-facing proof map
- [`docs/ARCHITECTURE.md`](./docs/ARCHITECTURE.md) — current contract architecture
- [`docs/SEMANTIC_ATOMICITY.md`](./docs/SEMANTIC_ATOMICITY.md) — guarantee boundary
- [`docs/STATE_MACHINE.md`](./docs/STATE_MACHINE.md) — lifecycle and recovery
- [`docs/EVIDENCE_MODEL.md`](./docs/EVIDENCE_MODEL.md) — evidence and consensus model
- [`docs/ACCOUNTING_MODEL.md`](./docs/ACCOUNTING_MODEL.md) — escrow and conservation
- [`docs/THREAT_MODEL.md`](./docs/THREAT_MODEL.md) — adversarial analysis
- [`docs/DEPLOYMENT_LOG_STUDIO_DEV.md`](./docs/DEPLOYMENT_LOG_STUDIO_DEV.md) — live proof
- [`tests/`](./tests) — deterministic, runtime, backend, frontend, and E2E verification

## Reproduce locally

Python verification is pinned to Python 3.12 in [`pyproject.toml`](./pyproject.toml) and [`uv.lock`](./uv.lock).

```sh
uv sync --frozen
uv run python -m pytest -q
```

Frontend:

```sh
npm ci
npm run typecheck
npm run test
npm run build
```

For the exact certified runtime/environment record, see [`docs/LOCAL_VERIFICATION.md`](./docs/LOCAL_VERIFICATION.md).

## Scope and limitations

COMMIT's guarantee covers settlement rights held by the protocol. External systems are modeled as reservations, idempotent adapters, or compensatable effects rather than magically reversible operations.

The current public Studio Dev proof demonstrates finalized COMMIT and ABORT branches and one-time entitlement consumption. It does not claim authenticated proof of downstream external delivery or production-grade retry/reconciliation for failed external transfers.

See [`docs/OPEN_QUESTIONS.md`](./docs/OPEN_QUESTIONS.md) for the concise submission boundary.

## Agent Tank

COMMIT is built for the **agentic economy**: autonomous participants can coordinate around subjective real-world evidence without allowing an unbound AI judgment to directly control economic consequences.

Official event: https://portal.genlayer.foundation/agent-tank/
