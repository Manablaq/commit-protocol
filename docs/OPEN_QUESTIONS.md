# Verification Gates

Updated 2026-09-10. This ledger distinguishes completed local hardening from
remaining target-network proof.

| ID | Question | Current evidence | Closing condition |
| --- | --- | --- | --- |
| ENV-01 | What network does Agent Tank require? | Rendered submission form inspected 2026-09-09: Studio, Bradbury or Asimov address links supported; no exclusive Bradbury requirement shown | Closed for visible form; recheck at submission |
| ENV-02 | Are the selected target networks identified correctly? | Official docs and live CLI check distinguish Bradbury (`https://rpc-bradbury.genlayer.com`, chain 4221) from Studio dev (`https://studio-dev.genlayer.com/api`, chain 61997) | Use only the selected network’s current metadata and canary receipts |
| ENV-03 | Exact Studio Dev, consensus and GenVM runtime? | Matching RC CLI `0.40.0-rc.3`, Studio Dev chain 61997, v0.6 `5jyc...` runner, and source-matched canary/full COMMIT deployments verified 2026-09-10 | Closed for the deployed source; keep network-specific receipts in the Studio Dev deployment log |
| SDK-01 | Transaction Kit package location? | Official GitHub pkg/core at 7a32d40a3e0c1d9962491b7e78423e2b969848ef | Location resolved; floating SDK dependency needs lock/testing when used |
| EVAL-01 | Which consensus primitive and result shape exist on Studio Dev? | The extracted v0.6 runtime exposes and locally executes `gl.vm.run_nondet`; the live contract is deployed but semantic evaluation has not yet run | Confirm the same API/result shape in a successful Studio Dev evaluation transaction before enabling live custody |
| FIN-01 | Does a zero-value finalized self-message authenticate and recover safely? | The modern v0.6 direct probe confirms emitted stage/value/calldata plus self-sender, identifier, replay guards, and harmless stale callbacks after recovery; Studio Dev proof is absent | Confirm callback receipt and read state showing one applied request; then execute failure and recovery-race cases |
| PAY-01 | Can failed external payment be proven and retried without loss or duplication? | Docs describe delayed messages; no tested external failure recovery | Inspect deployed ghost/consensus behavior; verify failure and retry |
| TIME-01 | Can reservations remain binding through variable finality? | Contract expiry uses the documented transaction-pinned standard-library clock and passes warped direct-runtime tests; live mission deadlines and effect expiry are stored on Studio Dev | Verify timestamp behavior and supplier reservation enforcement through live finality; test expiry against unresolved finality |
| EVID-01 | Can fetch enforce redirect and publisher path constraints? | Structural authority/path checks, active authority, v2 snapshot binding, bounded body, and distinct IDs pass local runtime tests; inspected fetch API exposes status, headers and body, not a verified final URL | Verify issuer-signature alternative in packaged runtime, or prove redirect behavior on the target network |

## Work permitted while gates remain open

Specification, adversarial design review, source inspection, direct-runtime testing, and read-only network checks. A canary must be narrowly scoped and use test funds only with known fee bounds. No frontend or production-readiness claim. Architecture dependent on an unanswered question remains a proposal.

## Next implementation sequence

Use the matching v0.6 RC stack on Studio Dev. The canary, full deployment,
authority registration, mission creation, payable funding, and effect
preparation are complete. Next execute evidence registration, sealing,
semantic evaluation, finality-gated allocation, claim dispatch, and recovery
canaries. Close FIN-01/PAY-01 and choose the final evidence provenance proof.
A self-contained accounting model and direct-runtime tests cannot substitute
for network proof.
