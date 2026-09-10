# COMMIT Studio Dev Deployment Log

Updated: 2026-09-10 (Africa/Lagos)

This log records only facts observed against Studio Dev. `ACCEPTED` means the
consensus transaction reached a decided accepted result; a separate finalized
receipt is required for the finality-gated callback and payment claims.

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

## Fee evidence

The current Studio Dev fee policy was read from the network, and exact fee
quotes were obtained with the matching RC toolchain before writes. The
payable funding write used `613816800010352` wei for protocol fees plus
`100000000000000` wei of mission value. Fee quotes are network- and payload-
dependent; clients must estimate again for each concrete call.

## Remaining live gates

The following are not claimed by this log: published evidence fetch,
`register_evidence`, `seal_mission`, `evaluate_mission`, finalized self-message
delivery and allocation, `claim_mission`, external transfer reconciliation,
and deadline recovery. The fixture records in `evidence/` are test evidence,
not proof of independent real-world issuer identity. Final redirect
verification and cryptographic issuer signatures remain outside this revision.
