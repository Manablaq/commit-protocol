# External GEN delivery observation

Status: implemented as a strict, read-only frontend observation path for the
certified Studio Next coordinator. This document does not change the
coordinator's onchain settlement boundary.

## What the product can prove

`claim_mission` is a one-way native-value dispatch. The coordinator consumes
the mission entitlement before dispatch and writes one `DISPATCHED` withdrawal
record. The frontend records the parent claim transaction locally, then uses
GenLayer JS `getTriggeredTransactionIds({ hash })` to locate the child
transaction created by the external message.

Before inspecting a child, the observer independently verifies all of these
parent facts:

1. the parent targets the certified Studio Next coordinator;
2. `from_address`, `sender`, and `origin_address` all match the connected
   beneficiary;
3. the decoded method is exactly `claim_mission` and its mission ID matches
   the selected mission;
4. the parent is `FINALIZED` with `FINISHED_WITH_RETURN`; and
5. exactly one positive native outbound message is exposed, with the exact
   beneficiary and message amount.

It then reports `DELIVERED` only when all of these child facts are present:

1. exactly one triggered child transaction ID is returned;
2. the child transaction is readable;
3. its recipient matches the connected beneficiary address;
4. its value matches the exact amount in the verified parent message;
5. its stored status is `FINALIZED`; and
6. its execution result is `FINISHED_WITH_RETURN`.

A locally persisted amount is only a fail-closed consistency check; it is never
the source of truth. The parent transaction and its message are read from the
network.

## Fail-closed states

| Observation | Meaning | Product action |
| --- | --- | --- |
| `PENDING` | The exact child exists but is not finalized. | Keep observing; never infer failure from elapsed time. |
| `DELIVERED` | Exact recipient, amount, finality, and successful execution match. | Show delivery as observed. |
| `FINALIZED_ERROR` | Exact recipient and amount match, but finalized child execution failed. | Show that execution errored; do not call it terminal non-delivery, restore, or retry automatically. |
| `UNVERIFIED` | No child ID, malformed/ambiguous child set, unreadable child, mismatched recipient/value, unknown result, or RPC failure. | Show that delivery is unresolved; do not infer success or terminal non-delivery. |

The UI exposes an explicit `Observe child transaction` action and keeps the
parent claim ID, exact mission ID, beneficiary, and amount in beneficiary-scoped
browser storage. It also accepts a manually pasted parent claim ID for recovery
after storage is cleared. Every supplied ID is re-read and re-bound to the
network transaction before any status is shown; switching wallets cannot
surface another wallet's claim observation.
Browser storage is only a convenience cache; it is not trusted contract state.

## What this intentionally does not claim

The observer does not create a contract callback, cryptographic delivery
receipt, refund, retry, or rollback. It contains no write method and the UI
contains no automatic retry button. A child timeout, missing child ID, or
ambiguous RPC response remains `UNVERIFIED`.

This boundary is required by the current GenLayer architecture: external
messages are asynchronous, do not return a value to the parent, and attached
value is not automatically restored when a child execution fails. Studio Next
also does not provide the recipient-layer EVM contract interaction required
for an idempotent payout vault. See the official [messages
documentation](https://docs.genlayer.com/developers/intelligent-contracts/features/messages),
[value transfer documentation](https://docs.genlayer.com/developers/intelligent-contracts/features/value-transfers),
and [Studio limitations](https://docs.genlayer.com/developers/intelligent-contracts/tools/genlayer-studio/limitations).

Therefore the certified coordinator continues to expose
`external_withdrawal_recovery: false`. Adding a timeout-based retry or a caller
supplied “transfer failed” flag would create a double-payment race and would
be weaker than the current fail-closed behavior.

## Verification

The implementation is in [`lib/genlayer-delivery.ts`](../lib/genlayer-delivery.ts)
and is covered by
[`tests/frontend/genlayer-delivery.test.ts`](../tests/frontend/genlayer-delivery.test.ts).
The tests cover parent target/caller/method/mission binding, exact outbound
message binding, successful finalization, finalized execution failure, pending
children, missing and ambiguous child IDs, malformed reads, recipient/value
binding, tampered local amounts, and beneficiary-scoped persistence.

Run the frontend gates from the repository root:

```sh
npm run typecheck
npm run lint
npm run test
npm run build
```

The hosted application remains the canonical
[`https://commit-protocol.vercel.app`](https://commit-protocol.vercel.app)
deployment and continues to target the certified Studio Next coordinator.
