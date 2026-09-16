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

### Historical published exact-source deployment

The currently published coordinator release is the previous release, recorded
through the SDK-compatible Studio Dev endpoint. It is not the current-source
submission deployment:

- Network: **GenLayer Studio development preview (historical release)**
- Recorded RPC: `https://studio-dev.genlayer.com/api`
- Chain ID: `61997` / `0xf22d`
- Contract: `0x7C1e450333D97CD4E02F48c3424BF10112697A60`
- Deployment transaction:
  `0x496654c019c07ffeed87fb8021e482d18f5da125c2388538d5ea88d81a6a7640`
- Deployment status: `FINALIZED`
- Execution result: `FINISHED_WITH_RETURN`
- Coordinator source SHA-256:
  `be0ef1686314354ac1b87ccd50ab42f0c933c312a4980c0e5479f2d3037e4e58`
- Deployed code: **19,670 bytes**
- Exact deployed-source match: **confirmed**
- Release commit: `e9858985495111cf2f21db6dc847c7f75b79c0da`

The current-source Agent Tank submission target is **Studio Next** at
`https://studio-next.genlayer.com/api` on chain `61997`. The browser integration
uses an explicit Studio Next chain object and does not select the SDK's
historical Studio Dev endpoint. The current source-bound deployment and
lifecycle proof use the explicit three-rotation Studio Next envelope.

See
[`docs/LIVE_STUDIO_NEXT_LIFECYCLE_2026-09-16.md`](./docs/LIVE_STUDIO_NEXT_LIFECYCLE_2026-09-16.md).

### Historical live COMMIT / ABORT proof

The earlier source-matched Studio Dev v0.7 deployment remains the recorded
end-to-end behavior proof for both policy outcomes:

- Contract: `0x10c708517b4465596E2dc40De92B30A610Cb7a10`
- Deployment transaction:
  `0x03071d2f8353c993a6a8aae38c1086e025df712f320090fd036ace2ef218ccab`
- Deployment result: `FINALIZED`, `FINISHED_WITH_RETURN`
- Source SHA-256:
  `4dd61b7e7a5acbdc254f7a63419fe7b4a2674909d49fa07e0d0b051fd74eb36f`

- **Mission 008 — COMMIT:** two bound evidence records were accepted, the
  finalized callback allocated the prepared entitlement, and the claim consumed
  that entitlement exactly once.
- **Mission 009 — ABORT:** one evidence record was ineligible, the finalized
  callback allocated the refund path, and the refund entitlement was consumed
  exactly once.

These historical lifecycle executions are not represented as executions of the
newer release commit.

See
[`docs/DEPLOYMENT_LOG_STUDIO_DEV.md`](./docs/DEPLOYMENT_LOG_STUDIO_DEV.md).

### Published application release

- Public application: `https://commit-protocol.vercel.app`
- Deployed application source commit:
  `f63c0cb19993b0ae79fffb34908fe3571bdfb768`
- Deployed application source tree:
  `31af728d04d39608bfd2c21932a1d201cdae2c73`
- Vercel production deployment:
  `dpl_9KCsNE68QaDZrYLcE9M2FGbH5vzn`
- Served coordinator: `0xEE21cCFF8f3755487f774BFd5Da9Ff51D5688581`
- Production smoke checks: `/`, `/app`, `/verify`, health, typed index lookup,
  typed transaction lookup, security headers, and browser verification action:
  **passed**

The complete production release record is in
[`docs/PRODUCTION_RELEASE_2026-09-16.md`](./docs/PRODUCTION_RELEASE_2026-09-16.md).


### Current reviewer-hardening release

A source-changing hardening release is deployed and certified on Studio Next:

- coordinator SHA-256:
  `e235731ac223ee136b06b8cfc332065927a03553a3b1f5531571cd4d5da119c6`
- coordinator bytes: `19873`
- helper SHA-256:
  `dfb564fbd644fae756808fee2afc1f43c35d0dde095e33ad9f4802569e80007a`
- Direct Runtime: **117 passed**
- Python non-runtime: **454 passed + 334 subtests**
- frontend Vitest: **27 passed**
- browser E2E: **12 passed**

The candidate rejects future-dated evidence, exposes the exact helper binding,
requires direct-origin claims, repairs the hosted verification read path, and
aligns the frontend SDK with the current Consensus v0.6 release family.

The certified replacement coordinator is
`0xEE21cCFF8f3755487f774BFd5Da9Ff51D5688581`, deployed in transaction
`0xc0e377d7a76893c253d61fcce42a320c6f5f41e5afad013a59dcbd279a998a50` with
`FINALIZED`, `FINISHED_WITH_RETURN`, `MAJORITY_AGREE`, and rotations `[3]`.
The earlier zero-rotation deployment at
`0x597641c88a3644f2C8c5c0baD9F1072710a82E85` remains historical failure
evidence only.


## Security properties

COMMIT is designed around the failure modes that matter when AI consensus can move economic state:

- authenticated evidence authority and issuer binding;
- immutable mission/evidence identity and version binding;
- freshness and expiry constraints;
- distinct authenticated-issuer corroboration requirements;
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
- [`docs/DEPLOYMENT_LOG_STUDIO_DEV.md`](./docs/DEPLOYMENT_LOG_STUDIO_DEV.md) — historical live proof
- [`docs/CURRENT_DEPLOYMENT_PROOF_2026-09-16.md`](./docs/CURRENT_DEPLOYMENT_PROOF_2026-09-16.md) — historical published-release deployment proof
- [`docs/LIVE_STUDIO_NEXT_LIFECYCLE_2026-09-16.md`](./docs/LIVE_STUDIO_NEXT_LIFECYCLE_2026-09-16.md) — current source-bound deployment and lifecycle proof
- [`docs/STUDIO_NEXT_DEPLOYMENT_ENVELOPE.md`](./docs/STUDIO_NEXT_DEPLOYMENT_ENVELOPE.md) — target identity and rotation invariant
- [`docs/STUDIO_NEXT_CHECKPOINT_2026-09-15.md`](./docs/STUDIO_NEXT_CHECKPOINT_2026-09-15.md) — superseded historical pre-deployment checkpoint
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

The current source-bound Studio Next proof demonstrates finalized COMMIT and
ABORT branches and one-time entitlement consumption. It does not claim
authenticated proof of downstream external delivery or production-grade
retry/reconciliation for failed external transfers.

See [`docs/OPEN_QUESTIONS.md`](./docs/OPEN_QUESTIONS.md) for the concise submission boundary.

## Agent Tank

COMMIT is built for the **agentic economy**: autonomous participants can coordinate around subjective real-world evidence without allowing an unbound AI judgment to directly control economic consequences.

Official event: https://portal.genlayer.foundation/agent-tank/
