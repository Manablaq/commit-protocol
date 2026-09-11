# State Machine and Privileges

Status: revision `0.7.0-reviewable-manifest` is implemented and directly tested
locally. It adds one bounded read surface for the exact effect/evidence inputs
and registered authority metadata behind both sealed roots. Studio Dev semantic
consensus, finalized callback allocation, and finalized claim dispatch are
proven for the prior source by mission-004; this revision requires a fresh
source-matched deployment and live proof. External delivery reconciliation,
recovery, and live deadline races remain open.

Contract state and transaction consensus status are separate. An accepted
transaction may expose provisional state. A stored word such as COMMITTED is
not standalone proof of finality.

| From | Action / caller | Guards | Result |
| --- | --- | --- | --- |
| Absent | `create_mission` / principal | Unique mission ID; supported policy digest; valid immutable terms and deadlines | `PREPARING` |
| PREPARING | `fund_mission` / principal | Payable positive value; preparation deadline; budget cap | Increased native-GEN escrow |
| PREPARING | `authorize_supplier` / principal | Exact nonzero supplier; before preparation deadline | Supplier may prepare effects |
| PREPARING | `revoke_supplier` / principal | No prepared effect owned by that supplier | Supplier authorization disabled |
| PREPARING | `prepare_effect` / principal or authorized supplier | Exact digest; positive bounded value; valid beneficiary/expiry | Root effect |
| PREPARING | `prepare_effect_with_dependency` / principal or authorized supplier | Same checks plus existing earlier dependency | Child effect in bounded single-parent graph |
| PREPARING | `register_evidence` / principal | Active registered authority; exact HTTPS origin/path; mission subject; expiry through recovery boundary | Evidence manifest entry |
| PREPARING | `seal_mission` / principal | Funding, effects, two distinct registered origin/path pairs, matching roots, acyclic graph | Immutable `SEALED` snapshot |
| PREPARING | `cancel_mission` / principal | No sealed obligations | Abort allocation and refund entitlement |
| SEALED | `evaluate_mission` / anyone | Recovery deadline not reached; exact v2 records independently re-read | `DECISION_PENDING`; zero-value finalized self-message emitted |
| DECISION_PENDING | `apply_decision` / authenticated coordinator self-message | Exact decision nonce; allocation not already applied | `COMMITTED` or `ABORTED` allocation |
| PREPARING / SEALED / DECISION_PENDING | `expire_mission` / anyone | Recovery deadline reached; no terminal allocation | `ABORTED` allocation and refund entitlement |
| Allocated | `claim_mission` / beneficiary | Available beneficiary entitlement; fresh withdrawal ID | `DISPATCHED` withdrawal and finalized external GEN transfer requested |

The current supported policy is deliberately explicit:
`all-evidence-and-effects-v1`. Every evidence record must bind the exact
mission, objective, policy rule/digest, intent digest, effect root, authority,
URL, subject, expiry, and a complete boolean claim for every sealed effect.
COMMIT is returned only when every independently fetched record and every effect
claim is eligible. The contract does not currently invoke an LLM or interpret
an arbitrary policy document.

The apply-decision mechanism authenticates the self-message sender, binds the
exact decision nonce, and is idempotent. Cancellation and recovery are explicit
ABORT decisions with reason codes. If deadline recovery wins first, it replaces
any unresolved decision with `ABORT`; a late authenticated callback is harmless
even with stale calldata. This race still requires a live target-network proof.

Evaluation is permissionless after sealing. This removes an unnecessary keeper
dependency while preserving principal-only preparation, funding, evidence
registration, sealing, and cancellation.

External claim dispatch is intentionally not blindly retried. The entitlement
is consumed before dispatch to prevent double payment, and remains represented
by the finalized external message because an authenticated delivery/non-
delivery mechanism is not exposed by the current contract. The current
revision does not provide reconciliation or retry.

No upgrade/admin escape hatch can rewrite a sealed mission or redirect custody.
The owner can register or deactivate publisher authorities; deactivation blocks
new evidence and does not rewrite already stored history. Supplier
authorization is mission-scoped and cannot be revoked after that supplier has
prepared an effect.
