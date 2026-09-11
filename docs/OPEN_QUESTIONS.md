# Verification Gates

Updated 2026-09-11. This ledger distinguishes the locally verified and
source-matched Studio Dev deployment of `0.7.0-reviewable-manifest` from
remaining target-network and production-safety proof.

| ID | Question | Current evidence | Closing condition |
| --- | --- | --- | --- |
| ENV-01 | What network does Agent Tank require? | Rendered submission form inspected 2026-09-09: Studio, Bradbury or Asimov address links supported; no exclusive Bradbury requirement shown | Closed for visible form; recheck at submission |
| ENV-02 | Are the selected target networks identified correctly? | Official docs and live CLI check distinguish Bradbury (`https://rpc-bradbury.genlayer.com`, chain 4221) from Studio dev (`https://studio-dev.genlayer.com/api`, chain 61997) | Use only the selected network’s current metadata and canary receipts |
| ENV-03 | Exact Studio Dev, consensus and GenVM runtime? | Matching RC CLI `0.40.0-rc.3`, Studio Dev chain 61997, v0.6 `5jyc...` runner, and source-matched v0.7 deployment at `0x10c708...7a10`; deployed bytes and local bytes both 61,306 with SHA-256 `4dd61b...eb36f` | Recheck after any network or runner upgrade |
| SDK-01 | Transaction Kit package location? | Official GitHub pkg/core at 7a32d40a3e0c1d9962491b7e78423e2b969848ef | Location resolved; floating SDK dependency needs lock/testing when used |
| EVAL-01 | Which consensus primitive and result shape exist on Studio Dev? | Mission 008 evaluation `0x349b...ae4e` reached `FINISHED_WITH_RETURN`, `COMMIT`, and exact envelope readback; mission 009 evaluation `0x1ba6...2dbb` reached `FINISHED_WITH_RETURN`, `ABORT`, and exact envelope readback | Cover validator disagreement/appeal behavior and recheck after protocol upgrades |
| FIN-01 | Does a zero-value finalized self-message authenticate and recover safely? | Mission 008 callback `0x349d...7d8f` finalized and applied COMMIT once; mission 009 callback `0x404e...37e1` finalized and applied ABORT once. Direct runtime also covers replay and late-callback guards | Live deadline-recovery race and a live stale-callback case remain unexecuted |
| PAY-01 | Can failed external payment be proven and retried without loss or duplication? | v0.7 mission-008 claim `0xee8044...0190c` and mission-009 refund claim `0xb9a026...923a8` finalized external children with exact values; internal entitlements became zero. The contract has no authenticated reconciliation/retry path | Add and test an authenticated delivery/non-delivery proof and a one-time retry or recovery path before production custody |
| TIME-01 | Can reservations remain binding through variable finality? | Contract expiry uses the documented transaction-pinned standard-library clock and passes warped direct-runtime tests; live mission deadlines and effect expiry are stored on Studio Dev; local recovery now records an explicit ABORT reason | Verify timestamp behavior and supplier reservation enforcement through live finality; test expiry against unresolved finality |
| EVID-01 | Can fetch enforce redirect and publisher path constraints? | Structural authority/path checks, active authority, v2 snapshot binding, bounded body, and distinct IDs pass local runtime tests; inspected fetch API exposes status, headers and body, not a verified final URL | Verify issuer-signature alternative in packaged runtime, or prove redirect behavior on the target network |

## Work permitted while gates remain open

Specification, adversarial design review, source inspection, direct-runtime testing, and read-only network checks remain permitted. The live mission proof is test-fund evidence, not a production-readiness claim. Architecture dependent on an unanswered question remains a proposal.

## Next implementation sequence

Use the matching v0.6 RC stack on Studio Dev. The source-matched v0.7
deployment, authority registration, mission creation, payable funding, effect
preparation, evidence registration/fetch, sealing, semantic COMMIT/ABORT
evaluation, finality-gated allocation, reviewer manifest readback, and
finalized claim/refund dispatch are proven by missions 008 and 009. Remaining
release work is authenticated external-transfer reconciliation/retry, live
deadline-recovery races, and a stronger issuer provenance proof (verified final
URL or issuer-key signature). A self-contained accounting model and
direct-runtime tests cannot substitute for those remaining network proofs.
