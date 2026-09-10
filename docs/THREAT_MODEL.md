# Threat Model and Required Tests

Status: implementation review. Locally verified controls are backed by the direct-runtime suite; live/network-dependent controls remain unverified.

| Threat | Required control / recovery | Test obligation |
| --- | --- | --- |
| Malicious principal | Exact supplier consent; no unilateral mutation after seal | Change intent, policy, amount after preparation |
| Malicious agent / compromised sub-agent | Sender-based scoped authority; attenuated delegation | Expand budget, role, deadline or recipient set |
| Malicious supplier | Source provenance, independent corroboration, bounded claims | Authentic publisher lies; conflicting evidence blocks approval |
| Prompt injection | Evidence treated as data; fixed evaluator and tool scope | Record says to approve or redirect payment |
| Stale / fake evidence | Version, digest, authority and freshness checks | Expired record, forged signature, changed payload |
| Publisher substitution | Exact origin and scoped path; redirect enforcement | Shared host attacker path, userinfo, encoded traversal, redirect |
| Evidence reuse | Subject/mission/effect binding as appropriate | Valid evidence for another supplier or mission |
| Recipient / amount / calldata alteration | Canonical sealed effect root; renewed consent on revision | Mutate every consequential field independently |
| Root or mission-version substitution | Domain-bound decision envelope | Cross-version, cross-contract and cross-chain replay |
| Replay / double settlement / double refund | Unique nonces; one terminal allocation; idempotency | Deliver callback repeatedly and reorder recovery |
| Expired mission / effect | Explicit transaction-time policy and reservation commitment | Delayed finality after external offer expiry |
| Unresolved mission / trapped funds | Permissionless deadline recovery under network liveness | Lost callback, evaluation failure, submitter offline |
| Validator disagreement / leader manipulation | Independent evaluation; exact economic equivalence | Wrong well-formed leader COMMIT must fail |
| Child-message failure | Zero-value allocation callback; custody stays in coordinator | Callback fails with no asset loss; later recovery |
| Fee exhaustion | Profile every branch; separate fee and principal accounting | Insufficient child fee produces visible unresolved state |
| Partial payment | Atomic entitlement allocation; independent withdrawal records | One payment succeeds while another is delayed |
| Unknown transfer result | Reserve dispatched value; no blind retry | Timeout after actual delivery cannot pay again |
| Nested mission abuse | Scope and budget attenuation; cycle/reuse rejection | Child both claims own funds and parent allocation |
| Oversized / cyclic graph | Enforced resource bounds, acyclicity, bounded loops | Worst-case graph and payload fit measured execution budget |
| Admin compromise | No custody override or sealed-state rewrite | No method grants admin arbitrary withdrawal |
| Transaction-order/finality race | Test network rollback and callback ordering | Recovery and decision compete across appeal |

## Open high-severity findings

H-01: Withdrawal failure recovery and proof of non-payment are unverified. COMMIT consumes an entitlement before dispatch and intentionally exposes no blind retry, which prevents double payment but can leave a failed external child unresolved. Gate: real adapter failure tests and authenticated retry semantics.

H-02: Timestamp eligibility does not enforce real-world expiry at finality. Gate: explicit supplier hold-until-outcome terms or a verified reservation adapter.

H-03: Finalization callback authentication, replay protection, and transaction ordering are unverified on the selected stack. Gate: a minimal network canary before mission custody code.

H-04: Publisher redirect/path enforcement depends on the actual fetch API. Gate: source inspection and adversarial fetch tests, or verified issuer signatures.

No live fund-bearing deployment is approved while these network-dependent findings remain open.
