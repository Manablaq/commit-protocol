# State Machine and Privileges

Status: proposed; finality delivery assumptions require a canary test.

Contract state and transaction consensus status are separate. An accepted transaction may expose provisional state. A stored word such as COMMITTED is never standalone proof of finality.

| From | Action / caller | Guards | Result |
| --- | --- | --- | --- |
| Absent | create / principal | Unique nonce; valid immutable authority/time policies | PREPARING |
| PREPARING | fund / principal | Positive exact value; budget cap | PREPARING with increased escrow |
| PREPARING | propose / scoped agent or principal | Authorized role; valid graph; before preparation deadline | New revision; affected approvals invalidated |
| PREPARING | prepare / supplier | Exact effect digest, revision, reservation terms | Supplier receipt |
| PREPARING | seal / principal | Funded; every effect approved; acyclic graph; complete policy/evidence references | SEALED immutable snapshot |
| PREPARING | cancel / principal | No sealed obligations | Abort allocation |
| SEALED | evaluate / anyone | Eligible time; exact snapshot | Decision candidate or REPAIR_REQUIRED |
| REPAIR_REQUIRED | repair / principal plus affected suppliers | New revision; fresh authorization; original absolute recovery deadline retained | PREPARING |
| SEALED | valid evaluation completes | Independent semantic result; hard constraints pass for COMMIT | DECISION_PENDING; emit zero-value finalization message |
| DECISION_PENDING | apply decision / authenticated coordinator self-message | Exact current decision identity; unused allocation nonce; finalized-parent delivery | COMMITTED or ABORTED allocation |
| Unallocated states | recover / anyone | Recovery deadline reached; no terminal allocation; invalidate pending decision nonce | ABORTED allocation |
| Allocated | claim / beneficiary | Available entitlement; fresh withdrawal nonce | Withdrawal record DISPATCHED |
| DISPATCHED | reconcile / verified network mechanism | Proven delivery or proven non-payment/restoration | DELIVERED or entitlement restored |

The apply-decision mechanism is a design candidate: self-message sender authentication plus `on='finalized'` delivery must be supported and tested. The callback itself has its own consensus lifecycle. Only its successful finalized state is presented as durable allocation.

## Races

- Allocation and recovery serialize through one coordinator. If recovery wins, it invalidates the pending decision, and the delayed callback does nothing. If allocation wins, recovery cannot refund the same escrow.
- A failed evaluation leaves the prior snapshot recoverable. A timeout is not a semantic ABORT verdict.
- Repair cannot reopen a successful terminal decision, extend the original recovery deadline, or retain approvals for changed terms.
- Pending callback recovery must be tested against the network's actual transaction ordering; it is not assumed that later transactions can always overtake unresolved ones.
- Duplicate callbacks are idempotent and cannot change allocation or create new withdrawals.

## Privileges

Principal defines intent, delegates bounded preparation, funds, authorizes the final snapshot, and cancels before sealing. Agents can propose within scope but cannot allocate funds or attest to other suppliers. Suppliers authorize only their own precise effects. Anyone may pay to request evaluation or valid recovery; that confers no discretion over outcomes. Beneficiaries claim only their own allocations.

No upgrade/admin escape hatch may rewrite sealed missions or redirect custody. Nested delegation can only narrow the parent scope, budget, recipients, effect types, and deadline. Cycles and reuse of child allocations are rejected.
