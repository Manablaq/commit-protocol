# Verification Gates

Updated 2026-09-10. This ledger distinguishes completed investigation from remaining proof.

| ID | Question | Current evidence | Closing condition |
| --- | --- | --- | --- |
| ENV-01 | What network does Agent Tank require? | Rendered submission form inspected 2026-09-09: Studio, Bradbury or Asimov address links supported; no exclusive Bradbury requirement shown | Closed for visible form; recheck at submission |
| ENV-02 | Are the selected target networks identified correctly? | Official docs and live CLI check distinguish Bradbury (`https://rpc-bradbury.genlayer.com`, chain 4221) from Studio dev (`https://studio-dev.genlayer.com/api`, chain 61997) | Use only the selected network’s current metadata and canary receipts |
| ENV-03 | Exact Studio, consensus and GenVM runtime? | GenVM manager v0.6.0-rc4 release archive verified; Bradbury rejected the current `5jyc...` runner; corrected `1jb45...` canary reached `ACCEPTED / AGREE / FINISHED_WITH_RETURN`, and its live source hash matched the local probe | Close probe compatibility; separately deploy and verify the full COMMIT source |
| SDK-01 | Transaction Kit package location? | Official GitHub pkg/core at 7a32d40a3e0c1d9962491b7e78423e2b969848ef | Location resolved; floating SDK dependency needs lock/testing when used |
| EVAL-01 | Which custom equivalence API exists in the selected Bradbury runner? | The documented legacy source path and local legacy-runtime tests pass with `gl.vm.run_nondet`; the v0.6 `5jyc...` path is not available on Bradbury; the corrected canary reached `ACCEPTED` but does not call nondeterminism | Confirm the same API/result shape in a successful Bradbury evaluation transaction before enabling live custody |
| FIN-01 | Does a zero-value finalized self-message authenticate and recover safely? | Local legacy-runtime probe confirms emitted stage/value/calldata plus self-sender, identifier, and replay guards; corrected canary is deployed and callback transaction `0x221f...0101` was submitted | Confirm callback receipt and read `state()` showing one applied request; then execute failure and recovery-race cases |
| PAY-01 | Can failed external payment be proven and retried without loss or duplication? | Docs describe delayed messages; no tested external failure recovery | Inspect deployed ghost/consensus behavior; verify failure and retry |
| TIME-01 | Can reservations remain binding through variable finality? | Contract expiry uses the documented transaction-pinned standard-library clock and passes warped direct-runtime tests; reservation holdability through live finality remains unverified | Verify timestamp behavior and supplier reservation enforcement on the target network; test expiry against unresolved finality |
| EVID-01 | Can fetch enforce redirect and publisher path constraints? | Structural authority/path checks, mission-bound evidence, and distinct-authority sealing pass local runtime tests; inspected fetch API exposes status, headers and body, not final URL | Verify issuer-signature alternative in packaged runtime, or prove redirect behavior on the target network |

## Work permitted while gates remain open

Specification, adversarial design review, source inspection, direct-runtime testing, and read-only network checks. A canary must be narrowly scoped and use test funds only with known fee bounds. No frontend or production-readiness claim. Architecture dependent on an unanswered question remains a proposal.

## Next implementation sequence

Use the accepted canary to execute the minimal live callback proof; then deploy the full COMMIT source and execute evaluation, finality, payment, and recovery canaries. Close FIN-01/PAY-01 and choose enforceable evidence provenance. Payable custody and settlement are implemented locally but stay blocked for live funds until network proof closes the relevant gates. A self-contained accounting model and direct-runtime tests cannot substitute for network proof.
