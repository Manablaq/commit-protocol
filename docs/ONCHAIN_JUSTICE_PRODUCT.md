# COMMIT — Onchain Justice

Status: **implemented product layer over the certified COMMIT coordinator**
Date: 2026-09-16

## Product promise

COMMIT is an evidence-bound dispute and settlement layer for autonomous
commerce. It makes the full path visible:

```text
Agreement → Escrow → Evidence → Verdict → Appeal → Finality → Settlement
```

The product does not invent a second contract state machine. The Case Room
renders the coordinator's typed reads and, when an evaluation transaction is
provided, the authoritative GenLayer transaction lifecycle. The application
labels accepted decisions as provisional and treats `FINALIZED` plus a
successful execution result as the durable boundary.

## Implemented surfaces

### Landing page (`/`)

The landing experience explains the problem, the five-stage protocol path, the
trust model, the deployment identity, and the boundary of the guarantee before
the user enters the application. It supports light/dark mode, reduced-motion
behavior, responsive layout, and scroll-based reveal effects.

### Case Room (`/app`)

The Case Room is the working surface for a connected Studio Next wallet. It
reads the exact coordinator address configured in
`lib/deployment-anchor.ts` and exposes:

- mission and escrow facts;
- authenticated evidence records and their authority/version bindings;
- sealed effect and evidence roots;
- decision, allocation, and refund entitlement state;
- a derived lifecycle timeline whose labels come only from returned state;
- the exact evaluation transaction input used to read the GenLayer appeal
  lifecycle;
- the native appeal action, when the authoritative SDK says it is available.

When the evaluation flow creates a transaction, its exact transaction ID is
stored in browser-local state for that mission so the Case Room can offer a
continuous read path without asking the user to copy it again. This is only a
convenience cache; the network read remains authoritative.

### Verification center (`/verify`)

The verification center reads backend-indexed proof and typed transaction data.
It also presents the native appeal lifecycle as a read-only surface when the
user supplies a GenLayer transaction ID. It never submits an appeal from the
verification page.

## Native appeal implementation

The implementation in `lib/genlayer-appeal.ts` uses the installed GenLayer JS
SDK public methods:

1. `advanced.getTransactionLifecycle({ hash })` reads the authoritative
   lifecycle and decision identity.
2. `canAppeal({ txId })` determines whether the active decision is currently
   appealable.
3. `getAppealCharge({ txId })` reads the current total charge immediately before
   a possible appeal.
4. `appealTransaction({ txId })` performs the SDK's bound appeal operation.

The frontend does not guess a charge, manufacture an appeal state, use a timer
as finality, or wait for a decision to finalize before it can display an
accepted appeal submission. After submission it keeps the same transaction ID
as the source of truth and refreshes the lifecycle asynchronously.

## State vocabulary

The product intentionally distinguishes these states:

| UI label | Source of truth | Meaning |
| --- | --- | --- |
| Under validator review | lifecycle with no active decision | The evaluation is still processing. |
| Provisional verdict | active decision, no open appeal | A decision exists but durable finality is not established. |
| Appeal window open | `canAppeal(txId) === true` | The SDK says a challenge can be submitted now. |
| Appeal in progress | stored status `AppealCommitting` or `AppealRevealing` | Fresh validator work is underway. |
| Final verdict | stored status `Finalized` | The protocol lifecycle has reached durable finality. |

The Case Room's settlement card is separately bound to the coordinator's
allocation fields. A provisional verdict is never displayed as a paid
settlement.

## Security and truth boundary

The product inherits the coordinator's reviewer-hardening guarantees:

- authenticated and versioned evidence binding;
- mission, record, and effect-root binding;
- freshness, future-time, and expiry checks;
- distinct-issuer corroboration;
- finality-gated one-time allocation;
- deadline recovery and late-callback protection;
- consume-before-dispatch claim handling.

The product does not claim to make arbitrary external GEN delivery atomic. The
known platform boundary is documented in `docs/OPEN_QUESTIONS.md` and
`docs/SEMANTIC_ATOMICITY.md`: downstream transfer delivery and trustless
terminal-failure reconciliation require an idempotent recipient-layer vault or
another platform-supported delivery primitive that is outside the certified
Studio Next coordinator scope.

## Verification commands

From the repository root:

```sh
npm run typecheck
npm run lint
npm test
npm run build
npm run test:e2e
```

The backend and contract evidence remain covered by the Python/runtime gates
described in `docs/LOCAL_VERIFICATION.md` and the Studio Next lifecycle record.
