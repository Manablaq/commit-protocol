# Verification Gates

Updated 2026-09-11. This ledger distinguishes the locally verified
`0.6.0-semantic-receipt` candidate and the prior revision's verified
`live-mission-004` Studio Dev path from remaining target-network and
production-safety proof.

| ID | Question | Current evidence | Closing condition |
| --- | --- | --- | --- |
| ENV-01 | What network does Agent Tank require? | Rendered submission form inspected 2026-09-09: Studio, Bradbury or Asimov address links supported; no exclusive Bradbury requirement shown | Closed for visible form; recheck at submission |
| ENV-02 | Are the selected target networks identified correctly? | Official docs and live CLI check distinguish Bradbury (`https://rpc-bradbury.genlayer.com`, chain 4221) from Studio dev (`https://studio-dev.genlayer.com/api`, chain 61997) | Use only the selected network’s current metadata and canary receipts |
| ENV-03 | Exact Studio Dev, consensus and GenVM runtime? | Matching RC CLI `0.40.0-rc.3`, Studio Dev chain 61997, v0.6 `5jyc...` runner, and source-matched canary/full COMMIT deployments verified 2026-09-10; `0.6.0-semantic-receipt` local candidate is not yet deployed | Closed for revision `0.5.0`; repeat deployment/source verification for `0.6.0` |
| SDK-01 | Transaction Kit package location? | Official GitHub pkg/core at 7a32d40a3e0c1d9962491b7e78423e2b969848ef | Location resolved; floating SDK dependency needs lock/testing when used |
| EVAL-01 | Which consensus primitive and result shape exist on Studio Dev? | Prior live evaluation `0x52ff...24cbf3` reached `ACCEPTED / FINISHED_WITH_RETURN / MAJORITY_AGREE`; local `0.6.0` now compares revision, roots, policy rule, and manifest counts in addition to the decision | Repeat the full envelope on the new deployment and cover validator disagreement/appeal behavior |
| FIN-01 | Does a zero-value finalized self-message authenticate and recover safely? | `live-mission-004` emitted nonce `8e9981...55a23f`; callback `0x045b...770c81` finalized and applied allocation once. Direct runtime also covers replay and late-callback guards | Live deadline-recovery race and a live stale-callback case remain unexecuted |
| PAY-01 | Can failed external payment be proven and retried without loss or duplication? | Claim `0xeaf0...044d53` finalized and emitted the exact external message; internal entitlement became zero. Studio Dev returned no child transaction ID and the contract has no authenticated reconciliation/retry path | Add and test an authenticated delivery/non-delivery proof and a one-time retry or recovery path before production custody |
| TIME-01 | Can reservations remain binding through variable finality? | Contract expiry uses the documented transaction-pinned standard-library clock and passes warped direct-runtime tests; live mission deadlines and effect expiry are stored on Studio Dev; local recovery now records an explicit ABORT reason | Verify timestamp behavior and supplier reservation enforcement through live finality; test expiry against unresolved finality |
| EVID-01 | Can fetch enforce redirect and publisher path constraints? | Structural authority/path checks, active authority, v2 snapshot binding, bounded body, and distinct IDs pass local runtime tests; inspected fetch API exposes status, headers and body, not a verified final URL | Verify issuer-signature alternative in packaged runtime, or prove redirect behavior on the target network |

## Work permitted while gates remain open

Specification, adversarial design review, source inspection, direct-runtime testing, and read-only network checks remain permitted. The live mission proof is test-fund evidence, not a production-readiness claim. Architecture dependent on an unanswered question remains a proposal.

## Next implementation sequence

Use the matching v0.6 RC stack on Studio Dev. The canary, full deployment,
authority registration, mission creation, payable funding, effect preparation,
evidence registration/fetch, sealing, semantic evaluation, finality-gated
allocation, and finalized claim dispatch are proven by the mission-004 record.
The next release work is source-matched deployment of `0.6.0-semantic-receipt`,
then authenticated external-transfer reconciliation/retry, live
deadline-recovery races, and a stronger issuer provenance proof (verified final
URL or issuer-key signature). A self-contained accounting model and
direct-runtime tests cannot substitute for those remaining network proofs.
