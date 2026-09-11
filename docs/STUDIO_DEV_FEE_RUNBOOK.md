# Studio Dev Fee Runbook

Studio Dev v0.6 transactions must be profiled against the concrete call. A
transaction can reach consensus and still fail during execution when its
message-fee allocation does not match a message emitted by the contract. The
failed first evaluation of mission 008 demonstrated this exact case:
`fee no_matching_allocation`.

## Required rule

Use `estimateTransactionFeesForWrite` for every write that can emit a message,
then pass all three returned fields unchanged to `writeContract`:

```js
const estimate = await client.estimateTransactionFeesForWrite({
  account,
  address: contractAddress,
  functionName: "evaluate_mission",
  args: [missionId],
});

const txId = await client.writeContract({
  account,
  address: contractAddress,
  functionName: "evaluate_mission",
  args: [missionId],
  fees: {
    distribution: estimate.distribution,
    messageAllocations: estimate.messageAllocations,
    feeValue: estimate.feeValue,
  },
});
```

`evaluate_mission` emits a finalized internal `apply_decision` callback.
`claim_mission` emits a finalized external native-GEN transfer. The estimator
discovers and prices those allocations; fixed fee JSON without the returned
`messageAllocations` is not a valid production client pattern.

## Verification rule

After submission, check both the consensus status and
`txExecutionResultName === "FINISHED_WITH_RETURN"`. For a state-changing
mission call, read the state back and verify the expected transition. A
successful evaluation should first expose `DECISION_PENDING`, then its
finalized callback must change the mission to `COMMITTED` or `ABORTED`.

The Studio Dev proof for this repository used this sequence:

1. Mission 008: `COMMIT` → finalized callback → `COMMITTED` → one-time claim.
2. Mission 009: one ineligible evidence record → `ABORT` → finalized callback → `ABORTED` → one-time refund.

Read methods whose contract signature contains `gl.Address` must receive the
SDK's typed calldata-address value, not an ordinary JavaScript string. This is
an SDK encoding requirement, not a contract authorization shortcut.

Fee presets are payload- and network-dependent. Re-estimate after changing the
contract address, method, arguments, message shape, or network.
