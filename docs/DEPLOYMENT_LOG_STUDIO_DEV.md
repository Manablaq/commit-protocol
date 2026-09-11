# COMMIT Studio Dev Deployment Log

Updated: 2026-09-11 (Africa/Lagos)

This log records only facts observed against Studio Dev. `ACCEPTED` means the
consensus transaction reached a decided accepted result. Finalized receipts
are recorded separately where finality gates callback allocation or claim
dispatch.

## Network and toolchain

- Network: GenLayer Studio Dev preview
- RPC: `https://studio-dev.genlayer.com/api`
- Chain ID: `61997`
- Explorer: `https://explorer-studio-dev.genlayer.com/`
- Worker: `0x1f87Ae197af539253978d435aD45cCf28Fb95024` (`worker`)
- CLI: `genlayer 0.40.0-rc.3`
- SDK family: `genlayer-js 2.0.0-rc.1`
- Contract runner: `py-genlayer:5jycge4q8k23462jtb0b9fyey1s9qz928sz2nbrd9mg4sxqg2qng`

## Deployments

### Next candidate (not deployed)

- Source revision: `0.6.0-semantic-receipt`
- Local status: 24 deterministic tests, 78 direct-runtime tests, three lint targets, bytecode compilation, and diff checks passed on 2026-09-11.
- Deployment status: pending. The existing `0xf1a47118c04Ad0D5B49871ae207B8D715bC0d085` address remains the prior `0.5.0-authorized-graph` source and must not be cited as proof for this candidate.

### v0.6 canary

- Contract: `0xFD79D0E2A0fdddF784a7bA01fA30134339fBD76E`
- Transaction: `0x3c8e6af05cf958df98afdaa7e0758531157a51250e28e925a36fde720cd5e249`
- Execution: `ACCEPTED`, `FINISHED_WITH_RETURN`
- Source SHA-256: `f58e94c9974db16c1976177aa8b8e3ccd58f5ab982cc9cf41ee6d014db136cb3`

### Full COMMIT source

- Contract: `0xf1a47118c04Ad0D5B49871ae207B8D715bC0d085`
- Transaction: `0x79945193eaf3a6b23e1ea03c9a79d6473e6d596a53166c30661f001491abdddf`
- Execution: `ACCEPTED`, `FINISHED_WITH_RETURN`
- Local/deployed source SHA-256: `3a02e4bf77cad4a65aed5e24294c5fa558b68736391868bf4db5869c0eac5a71`
- `protocol_info()` readback: revision `0.5.0-authorized-graph`, evidence schema `commit-evidence-v2`, policy `all-evidence-and-effects-v1`, supplier authorization required, single-parent acyclic graph, and external withdrawal recovery explicitly disabled.

## Live setup transactions

- `register_authority(studio-issuer-a, raw.githubusercontent.com, /Manablaq/commit-protocol/main/evidence/issuer-a)` — `0x533ce81b72900b9a32a6c3b0b7e525a7eaf67fd9d47e007160f6d3e856e27eb`; readback active.
- `register_authority(studio-issuer-b, raw.githubusercontent.com, /Manablaq/commit-protocol/main/evidence/issuer-b)` — `0x835324790e31d16cccc8d5c3acd64c1d2aa01879d747c760bce32566d0b1554d`; `FINALIZED`, accepted; readback active.
- `create_mission(live-mission-001, budget 0.001 GEN)` — `0x4a71c4a7edd9be03b557e5a5131565f8d04d466be6757071817ef02ba7af3887`; `ACCEPTED`, `FINISHED_WITH_RETURN`; mission readback `PREPARING`.
- `fund_mission(live-mission-001, value 0.0001 GEN)` — `0xdd12ac23c61b17b6a8c520c41ff85667140b0ba8edc44d3e6c707b27ac7d8074`; mission readback `funded_value = 100000000000000` wei.
- `prepare_effect(live-mission-001, effect-a, value 0.00005 GEN)` — `0xa09b4b83609dc00af5e66b4aae3f5749ec9fd6c6c902e42b641e9d482f4793c0`; effect readback and derived root verified.
- Derived effect root: `e1b6972122f1becccb9041a45f2bcb8bb7eec2720ac22fd2e7c3cc8d7a38be4e`.

### Full mission-004 lifecycle

This is the current end-to-end Studio Dev proof. All hashes below are the
transaction IDs returned by the network; state and lifecycle fields were read
back from the deployed contract and transaction API.

- Mission: `live-mission-004`
- Objective: `Autonomous procurement package with verified semantic atomicity`
- Principal/refund beneficiary: `0x1f87Ae197af539253978d435aD45cCf28Fb95024`
- Budget: `1000000000000000` wei; funded value: `100000000000000` wei
- Preparation deadline: `1789152210`; recovery deadline: `1789238610`
- Effect: `effect-procurement`, beneficiary worker, value `100000000000000` wei, expiry `1789242210`
- Intent digest: `57cad0dbeae27b12179e8f2fd4b38d78e5f15f22205e51704b5e0c44b94d1d97`
- Effect digest: `c1a4ac948bda3ee990b6f38bdc7c72230f8803ff41346dc5581d328eca46d15c`
- Effect root: `b8ebfa5c0f2d1c87f401b3c2b6b5c9ee66ac6790d67f20cd72e3769e05a2c585`
- Evidence root: `4229ec6e52516f93dfe735a58eabeb01ff91ed514d55b3498ccec2f0952e64fd`
- Evidence A URL: `https://raw.githubusercontent.com/Manablaq/commit-protocol/main/evidence/issuer-a/record-004.json`
- Evidence B URL: `https://raw.githubusercontent.com/Manablaq/commit-protocol/main/evidence/issuer-b/record-004.json`
- Evidence A registration: `0x0efc68e09633c65e9d15cf333bf10ed37d19ae06e492535045ebc6ac0ff7a6f0` — `ACCEPTED`, `FINISHED_WITH_RETURN`, `MAJORITY_AGREE`
- Evidence B registration: `0x355832ea97494adf1b48ee05400bdf079d99beab8d7302d9cf7098bd6d0a71c6` — applied; mission readback reports `evidence_count = 2`
- Create mission: `0x1fc649c1a2f89f5531ace455dc44a31097650c1c6d77044c71bcbe54c9ccb856` — `ACCEPTED`, `FINISHED_WITH_RETURN`, `MAJORITY_AGREE`
- Fund mission: `0x9f02bd93f4b31c3c4bc9fbc49105dcf980b5dd7178e88a44fd5361b17d4a3c54` — funding applied; the SDK wait timed out while the transaction was still at lifecycle status `1`, so the authoritative contract readback is used for the funded value
- Prepare effect: `0xff7ad6d1ef973e4e4fdf8a934dbcfcafec4c98e1ec45057119b4e07667dcbf51` — `ACCEPTED`, `FINISHED_WITH_RETURN`
- Seal mission: `0xc37dd14f201170edb86109eb1b32740f97d6b4840f8b62ae44ac26f3678a3793` — `ACCEPTED`, `FINISHED_WITH_RETURN`, `MAJORITY_AGREE`
- Evaluate mission: `0x52ffb7815b986b2c730dc6d6084df3aef21ba81672ab9f286b9c4cb30d24cbf3` — `ACCEPTED`, `FINISHED_WITH_RETURN`, `MAJORITY_AGREE`; emitted finalized self-callback nonce `8e9981eee3422634501f3893b171b986836fb465bbd7e1e3c34e80afad85523f`
- Finalized callback: `0x045b1ff10d57e68c4c0b323fa7dc64d4de80a0fdecfa0619ff554808f8770c81` — `Finalized`; mission readback became `COMMITTED`, `decision = COMMIT`, `allocation_applied = true`, `evaluation_count = 1`
- Claim mission: `0xeaf091fa8fca5ab6e5986cd944672b72e2e526b1c6c28aabce2bc56e08044d53` — `Finalized`, `FINISHED_WITH_RETURN`; emitted one external message for `100000000000000` wei to the worker
- Post-claim readback: `get_claimable(worker) = 0`; this proves the internal entitlement was consumed exactly once before dispatch. `getTriggeredTransactionIds` returned no child ID, so the external delivery cannot be independently reconciled through the exposed Studio Dev transaction API.
- Final mission readback: `state = COMMITTED`, `decision = COMMIT`, `allocation_applied = true`, `funded_value = 100000000000000`, `prepared_value = 100000000000000`, `evidence_count = 2`, `effect_count = 1`, `reason_code = all_sources_and_effects_eligible`.

## Fee evidence

The current Studio Dev fee policy was read from the network, and exact fee
quotes were obtained with the matching RC toolchain before writes. The
payable funding write used `613816800010352` wei for protocol fees plus
`100000000000000` wei of mission value. Fee quotes are network- and payload-
dependent; clients must estimate again for each concrete call.

## Remaining live gates

The following remain outside this log: authenticated external-transfer delivery
reconciliation, failed-payment recovery/retry, and deadline recovery on a live
mission. The fixture records are public test evidence rather than proof of
independent real-world issuer identity. Final redirect verification and
cryptographic issuer signatures remain outside this revision. The contract
therefore documents `external_withdrawal_recovery: false`; do not represent
the current one-way external dispatch as a production-grade recoverable
payment rail.
