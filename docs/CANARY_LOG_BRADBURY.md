# Bradbury Canary Log

## Finalized self-message probe

- Network: GenLayer Bradbury Testnet
- Chain ID: `4221`
- RPC: `https://rpc-bradbury.genlayer.com`
- Sender: `0x1f87ae197af539253978d435ad45ccf28fb95024` (`worker`)
- Source: `probes/finalized_callback.py`
- Submitted transaction: `0xb2009df95d75eecf5c6b29900c45f0fc02d360d57a16ac68b4c4cb9600172d59`
- Submitted: 2026-09-10 (local task time)
- Status at first bounded receipt check: not yet accepted; CLI reported numeric status `1` (`PENDING`)
- Status at second bounded receipt check: still not accepted; CLI reported numeric status `3` (`COMMITTING`)
- Latest bounded receipt check: still not accepted; CLI reported numeric status `2` (`PROPOSING`) and timed out before the requested `ACCEPTED` state
- Contract address: not available until deployment acceptance/finalization is verified

This is a canary submission only. It does not establish deployment success, finalized self-message delivery, callback state mutation, or COMMIT custody safety. Do not cite it as a successful live demo until the receipt, deployed address, source identity, callback transaction, finality, and state are independently checked.

The worker balance was `10.611703293728233196 GEN` before submission and `10.611306336209951396 GEN` after the bounded receipt check. The difference is recorded as an observed balance change, not as a final fee accounting statement.
