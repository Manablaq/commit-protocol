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

### v0.7 source-matched deployment

- Source revision: `0.7.0-reviewable-manifest`
- Contract: `0x10c708517b4465596E2dc40De92B30A610Cb7a10`
- Deployment transaction: `0x03071d2f8353c993a6a8aae38c1086e025df712f320090fd036ace2ef218ccab`
- Execution: `ACCEPTED`, `FINISHED_WITH_RETURN`; explorer status `FINALIZED`
- Local/deployed source bytes: `61306 / 61306`
- Local/deployed source SHA-256: `4dd61b7e7a5acbdc254f7a63419fe7b4a2674909d49fa07e0d0b051fd74eb36f`
- New capability: `get_mission_manifest` exposes the frozen mission terms, exact bounded effect/evidence inputs, sealed roots, current decision/allocation state, and registered authority metadata used for reviewer reconstruction; all protocol counters now use explicit overflow guards.
- `protocol_info()` readback: chain `61997`, revision `0.7.0-reviewable-manifest`, `commit-mission-manifest-v1`, `commit-mission-receipt-v1`, `run_nondet`, permissionless post-seal evaluation, exact HTTPS origin/path authority enforcement, and external withdrawal recovery explicitly disabled.

The v0.6 source-matched deployment below is historical evidence for revision
`0.6.0-semantic-receipt`; it is retained for lineage and is not evidence for
the current address.

### v0.6 source-matched deployment

- Contract: `0xfB15d38FB1Bb5ba44965BA9d2b527e8D742004fF`
- Transaction: `0x993d17d863af0c7ff98feeb046c2a63af66e0a19f55adbff8bd95933a7a3a774`
- Execution: `ACCEPTED`, `FINISHED_WITH_RETURN`
- Source revision: `0.6.0-semantic-receipt`
- Local/deployed source SHA-256: `789ff473ac8574ac15bf810ce8eb30dc7b7d6845fa69537c663fb148cc407dca`
- `protocol_info()` readback: Studio Dev chain `61997`, semantic evaluation enabled, `commit-decision-v2` envelope, `commit-mission-receipt-v1` receipt, exact HTTPS origin/path authority enforcement, permissionless post-seal evaluation, and external withdrawal recovery explicitly disabled.

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

### v0.7 mission-008 COMMIT and reviewer-manifest proof

This isolated mission uses the v0.7 deployment and the public `record-008.json`
fixtures. Its source records, intent, effect root, and evidence root are bound
to the mission and read back through `get_mission_manifest`.

- Mission: `review-mission-008`
- Objective: `Autonomous procurement proof on COMMIT 0.7`
- Create: `0xb963e78313583ad6b79d475766350b97b3c8fa256bb3584c8ce4c1324fbeccd0`
- Fund: `0x4c9856c1aa984347554e0b9dc23f87859f7352db785b63828220cc46a587dfd0`
- Prepare effect: `0xbc2a92169683e3fedbdae9a5bde3cccf8672914566e48ac0c5a9fe41f56d3a9e`
- Evidence A: `0x499e4c1e7517ac4339ce5b63e181774ffc08d7ed876086b05a5cb0fd15a96136`
- Evidence B: `0xf42ff6416dd3e172dc0513f5cb4e916220061e809afe2f2f90a163252b8a1a5d`
- Seal: `0x6280c3625c39480080242551b7ed20fd0ff2badb5aa11ddc9485170d218f9bcb`
- Intent digest: `ad5dcd862c0fc1eae45ea8c678998e8ad703d3f673fe5db7288a46bd6b9abfbb`
- Effect root: `76584ccb158a9ce0736e85a16285fef47317d40f820b6894214e04347dc539ad`
- Evidence root: `1315a83d922eb06bc919f40e510619e4ef5849de5ff89949d273c6f36a3c58d4`
- Initial evaluation attempt: `0x25c31f76e6b2ee0021be7aeaf29146ce935d911133e87a3c302305a9e9e6cfa5` — finalized execution error `fee no_matching_allocation`; no contract state change. This is the fee-allocation failure documented in [STUDIO_DEV_FEE_RUNBOOK.md](./STUDIO_DEV_FEE_RUNBOOK.md).
- Corrected evaluation: `0x349b82f1385efb2e76c4e61e4664100eccf5ff853bf842982f2e13ea2daeae4e` — `FINISHED_WITH_RETURN`; `COMMIT`, `all_sources_and_effects_eligible`.
- Finalized callback: `0x349d463d3c043e4fb75fe7f6cd8fe48dd0e445868e7e02e7b191ffb084e27d8f` — `FINISHED_WITH_RETURN`; mission readback `COMMITTED`, `allocation_applied = true`.
- Claim: `0xee8044f4bd6ea0bacd69fe91bd8b4e21e03e0c370968511476fb53d29810190c`; finalized external child `0x2894a7973b0e8a5121f99ff334b0b036d1f9babb0875c7b1e3d8d1fae7fd4458` transferred `100000000000000` wei to the worker.
- Post-claim readback: mission claimable and global claimable balances are both `0`; the entitlement was consumed once.

### v0.7 mission-009 ABORT and one-time refund proof

This isolated mission uses the same deployed source and the public `record-009`
fixtures. Issuer A reports the effect as ineligible while issuer B reports it
eligible; the explicit all-records-and-effects policy therefore must abort.

- Mission: `review-mission-009`
- Objective: `Autonomous procurement abort proof on COMMIT 0.7`
- Create: `0x0843d26bfa6e07dc951ccfd26436642c1457a1b8817555c768aedd24ce0f07ce`
- Fund: `0xcef4d8d66d3c58aa3e0289bb0eb0719d7a3b8f8c6481a2eb735295f60011f91e`
- Prepare effect: `0xce94c60a2762d902e1fb428b8d6edfbd45a599a5c0051cba125b7ba8ef96e716`
- Evidence A: `0x9c9b2906806d375f7e5b63afdd4af0081f8f63c264dc02d942d24703e977e67a`
- Evidence B: `0x56aeb43e4c03c747d83047735677642b21df8571b33d5e4c36e9d3a845260351`
- Seal: `0xb39a91754e8591c68b5598a2d40ca22bb70c757c7c3ae90784bd850fe00df56c`
- Intent digest: `207ca483e2d7ff0bd21bd546182452b08ef42072966e09e267f64aee60c5b64c`
- Effect root: `592ba44fdc9f3b47f3b40107f17a8b4ac4f8413cb9c5a46f0e0691bc2d82c2af`
- Evidence root: `1471dbfea0463725323c87bdc083f939934255d94ece16183aeac3a67d48af5b`
- Evaluation: `0x1ba6a6fc7f646a1c945653740e0648354770e88b32f8b9d41b57afe08182dbbb` — `FINISHED_WITH_RETURN`; `ABORT`, `policy_or_source_ineligible`.
- Finalized callback: `0x404e8ed01f8347bf995f33d46e28675820d96afebb1b922a082b21b09df937e1` — `FINISHED_WITH_RETURN`; mission readback `ABORTED`, `allocation_applied = true`, refund entitlement `100000000000000` wei.
- Refund claim: `0xb9a026854d27a2b052588b3f32a876e3ed5583e7385bacef2a73ed70962923a`; finalized external child `0x4d9d327fc965dec177565a53893046a393176315a0829814e1dc1c7d81897d91` transferred `100000000000000` wei.
- Post-claim readback: mission claimable and global claimable balances are both `0`; the refund entitlement was consumed once.

## Fee evidence

The current Studio Dev fee policy was read from the network, and exact fee
quotes were obtained with the matching RC toolchain before writes. Message-
emitting calls used the SDK's network-generated `messageAllocations`; omitting
the finalized `apply_decision` allocation caused mission 008's first evaluation
to fail with `fee no_matching_allocation`. The corrected evaluation used a fee
value of `120158211300005176` wei plus one internal callback allocation. Claim
and refund calls used one external allocation. Fee quotes are network- and
payload-dependent; clients must estimate again for each concrete call.

## Remaining live gates

The following remain outside this log: authenticated external-transfer delivery
reconciliation, failed-payment recovery/retry, and deadline recovery on a live
mission. The fixture records are public test evidence rather than proof of
independent real-world issuer identity. Final redirect verification and
cryptographic issuer signatures remain outside this revision. The contract
therefore documents `external_withdrawal_recovery: false`; do not represent
the current one-way external dispatch as a production-grade recoverable
payment rail.
