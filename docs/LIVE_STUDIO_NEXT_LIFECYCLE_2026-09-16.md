# Current Studio Next deployment and lifecycle proof — 2026-09-16

This is the current source-bound proof for COMMIT. It records the finalized
replacement deployment and fresh COMMIT/ABORT lifecycle executions on GenLayer
Studio Next. All values below were read from the live Studio Next RPC after the
transactions settled.

## Release identity

- Repository: `https://github.com/Manablaq/commit-protocol`
- Repository HEAD: `6fe34484acb4bb21afd8f438ecac00e7780042e1`
- Coordinator source: `contracts/commit.py`
- Coordinator source: 19,873 bytes
- Coordinator SHA-256: `e235731ac223ee136b06b8cfc332065927a03553a3b1f5531571cd4d5da119c6`
- Helper source SHA-256: `dfb564fbd644fae756808fee2afc1f43c35d0dde095e33ad9f4802569e80007a`

The coordinator source read from the finalized deployment with
`gen_getContractCode` decodes to the same 19,873 bytes and the same SHA-256.
This is an exact source match, not a similarity check.

## Network and deployment

- Network: **GenLayer Studio Next**
- RPC used for submission and verification: `https://studio-next.genlayer.com/api`
- Chain ID: `61997` (`0xf22d`)
- Explorer: `https://explorer-studio-dev.genlayer.com/`
- Worker: `0x1f87Ae197af539253978d435aD45cCf28Fb95024`
- Coordinator: `0xEE21cCFF8f3755487f774BFd5Da9Ff51D5688581`
- Helper: `0x53405950e587Ca4F6232b4596f0992ea5aaD8Ae4`
- Deployment transaction: `0xc0e377d7a76893c253d61fcce42a320c6f5f41e5afad013a59dcbd279a998a50`
- Deployment status: `FINALIZED`
- Deployment execution: `FINISHED_WITH_RETURN`
- Deployment consensus: `MAJORITY_AGREE`
- Outer consensus rotations: `3`
- Fee-distribution rotations: `[3]`
- Deployment execution budget per round: `153643200000000`

`protocol_info()` on the finalized coordinator returned:

- protocol: `commit`
- revision: `0.7.0-reviewable-manifest`
- semantic evaluation: enabled
- evaluation trigger: `permissionless-after-seal`
- authority provenance: `https-origin-path`
- external withdrawal recovery: explicitly disabled
- helper address: `0x53405950e587Ca4F6232b4596f0992ea5aaD8Ae4`

## Fresh COMMIT lifecycle

Mission: `r12-commit-1789563760486-385024`

- Evaluation transaction: `0x6de9dcc572da4a9b68b3df99f2c3cd0f147310d92dcf7001e142d54c3596f522`
- Evaluation result: `FINALIZED / FINISHED_WITH_RETURN / MAJORITY_AGREE`
- Triggered callback count: exactly one
- Callback transaction: `0xaf5e16e055e24b9e19fdab7ebeac6c6f2a79f9b5cf770ad47e7eefe6fc19954b`
- Callback result: `FINALIZED / FINISHED_WITH_RETURN / MAJORITY_AGREE`
- Final mission state: `COMMITTED`
- Decision: `COMMIT`
- Decision reason: `all_sources_and_effects_eligible`
- Evaluation count: `1`
- Allocation applied: `true`
- Claim transaction: `0xd5ee347299c793b0fc2c6fdaeda392aa44597452ded74563ca55babd083a543a`
- Claim result: `FINALIZED / FINISHED_WITH_RETURN / MAJORITY_AGREE`
- Mission claimable after claim: `0`

The evaluation used two current-source evidence records bound to the mission,
two registered authorities, and one prepared effect. The finalized callback
applied the COMMIT allocation once before the claim was consumed.

## Fresh ABORT lifecycle

Mission: `r12-abort-1789563760486-537053`

- Evaluation transaction: `0xa95ad5fda9c6cc13fd6be44002f7c565a70b5358d1712d632fbe9cee9cd16b92`
- Evaluation result: `FINALIZED / FINISHED_WITH_RETURN / MAJORITY_AGREE`
- Triggered callback count: exactly one
- Callback transaction: `0x5b0d984efc88fa1ed3ac3672ca9305d8dbe5b8321091642afea0a175ebde37aa`
- Callback result: `FINALIZED / FINISHED_WITH_RETURN / MAJORITY_AGREE`
- Final mission state: `ABORTED`
- Decision: `ABORT`
- Decision reason: `policy_or_source_ineligible`
- Evaluation count: `1`
- Allocation applied: `true`
- Claim transaction: `0x7df93e138c158d8cea6179c88727f39b2be5bb968d98999f3d36b44a7c29858c`
- Claim result: `FINALIZED / FINISHED_WITH_RETURN / MAJORITY_AGREE`
- Mission claimable after claim: `0`

The ABORT path used the same sealed mission structure but included one
ineligible evidence payload. The finalized callback allocated the refund path
once, and the claim consumed it once.

## Final accounting readback

After both claims finalized, the coordinator returned:

- COMMIT mission claimable: `0`
- ABORT mission claimable: `0`
- Worker aggregate claimable: `0`
- Both missions remained in their expected terminal states.

## What this proves

This record proves, for the exact deployed coordinator source, the complete
tested path from sealed evidence through GenLayer semantic consensus, finalized
self-message application, terminal allocation, and one-time claim consumption
for both COMMIT and ABORT outcomes.

It does not claim that COMMIT can roll back arbitrary external systems or prove
delivery/reconciliation of an external transfer after native-value dispatch.
Those boundaries remain explicit in [`THREAT_MODEL.md`](./THREAT_MODEL.md) and
[`OPEN_QUESTIONS.md`](./OPEN_QUESTIONS.md).
