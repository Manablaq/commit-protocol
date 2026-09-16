# State Machine and Privileges

Status: revision `0.7.0-reviewable-manifest` is implemented, directly tested
locally, and deployed source-matched on Studio Next. It adds one bounded read
surface for the exact effect/evidence inputs and registered authority metadata
behind both sealed roots. Studio Next semantic consensus, finalized callback
allocation, finalized COMMIT claim dispatch, and finalized ABORT refund
dispatch are proven by the current-source lifecycle record. External delivery
reconciliation, recovery, and live deadline races remain bounded or separately
certifiable.

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
| PREPARING | `register_evidence` / principal | Existing authenticated attestation; exact authority/version and record/version; attested mission/version match; attested expiry covers recovery boundary | Evidence manifest entry |
| PREPARING | `seal_mission` / principal | Funding, effects, two evidence authorities controlled by distinct authenticated issuer addresses, matching roots, acyclic graph | Immutable `SEALED` snapshot |
| PREPARING | `cancel_mission` / principal | No sealed obligations | Abort allocation and refund entitlement |
| SEALED | `evaluate_mission` / anyone | Recovery deadline not reached; exact active v2 evidence independently re-read | Either persist an evidence-level `REPAIR_REQUIRED` response with no mission decision, or persist the exact active evaluation root and enter `DECISION_PENDING`; a zero-value finalized self-message is emitted only for a decision |
| SEALED | `repair_evidence` / principal | Existing `REPAIR_REQUIRED` failure; before recovery deadline; no mission decision; authenticated successor has the same authority/version, issuer, stable record ID, mission/version, and a strictly newer record version | Persist append-only `READY` repair; sealed evidence entry/root remain unchanged |
| SEALED | `evaluate_mission` / anyone after READY repair | Recovery deadline not reached; repaired active evidence independently re-read | Persist exact `evaluation_evidence_root`; enter `DECISION_PENDING` on a valid consequential result |
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

The sealed evidence root is immutable after sealing. Repair does not rewrite
that root. Reevaluation derives an active evidence root from the exact evidence
versions in force, and `commit-decision-v3` binds both the sealed and active
roots. `commit-mission-receipt-v2` and `commit-mission-manifest-v2` expose both
roots for reviewer verification.

A valid negative evidence record remains a semantic ABORT. Acquisition or
integrity failures use the repair path instead, and validator disagreement is
not stored as an evidence-source failure.

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
The owner can register or deactivate publisher authorities. Each authority ID
binds one immutable issuer address and version; issuer or version rotation
requires a new authority ID. Deactivation blocks new attestations and does not
rewrite already stored history. The current candidate is intended for a fresh
source-matched deployment and does not claim in-place storage-compatible
upgrading of the historical v0.7 contract. Supplier authorization is
mission-scoped and cannot be revoked after that supplier has prepared an
effect.
