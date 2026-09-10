# Accounting Model

Status: proposed; payment adapter and rollback tests are required before implementation approval.

## Conservation

For each mission, use disjoint buckets:

`F = L + C + R + D + W`

- F: cumulative recognized mission deposits.
- L: unallocated locked escrow.
- C: allocated, unwithdrawn supplier entitlements.
- R: allocated, unwithdrawn principal refunds, including unused COMMIT budget.
- D: dispatched value whose delivery is not yet authenticated.
- W: authenticated delivered value.

All buckets are nonnegative integer wei. C and R are current balances, not historical totals. Summing lifetime committed value and lifetime withdrawals would double count money. The initial four-term invariant is extended with D because GenLayer value messages can remain in flight.

## Transitions

| Operation | Accounting effect |
| --- | --- |
| Valid payable funding | F and L increase by the exact accepted call value |
| COMMIT allocation | L becomes zero; C increases by total agreed payouts; R receives the remainder |
| ABORT allocation | L becomes zero; R increases by all remaining L |
| Claim dispatch | Decrease that beneficiary's C or R; increase D; record immutable withdrawal ID, target, value |
| Verified payment success | Decrease D; increase W |
| Verified non-payment and funds restored | Decrease D; restore the same beneficiary entitlement |
| Ambiguous timeout | No monetary transition; keep D reserved |

The last two transitions require proof tied to the actual payment message and chain state. A caller assertion, absent explorer entry, timeout, or leader summary is insufficient. No recovery method accepting an arbitrary `success` boolean will exist.

## Custody and fees

Mission deposits enter only through explicit payable mission funding. Sender must be the mission principal in the initial design. Budget overfunding and arithmetic overflow are rejected before mutation. A plain unsolicited transfer does not authorize a mission deposit or increase a user's balance.

Protocol fee deposits are accounted separately from purchase principal. Caller transaction fees are not subtracted from mission escrow. Actual message fee behavior must be measured; if the network charges the ghost balance, the design requires a separate funded fee reserve before it can be approved.

Observed ghost balance must be reconciled against liabilities using network-specific treatment of in-flight messages. Do not assume `self.balance == L + C + R + D`: emitted value may already be held in a message.

## Withdrawal authority

Only the beneficiary can request a withdrawal of their entitlement. The target and amount become immutable when dispatched. No admin can change beneficiaries, sweep liabilities, or mark uncertain payments as failed. Address code/behavior can change; a claim that an address is an EOA does not itself prove transfers can never fail.

The withdrawal adapter is a release blocker until failure, finalization rollback, duplicate delivery, and retry semantics are tested against the selected network implementation.
