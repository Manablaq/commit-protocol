# Bradbury Canary Log

## Current result: v0.6 runner rejected by Bradbury

- Network: GenLayer Bradbury Testnet
- Chain ID: `4221`
- RPC: `https://rpc-bradbury.genlayer.com`
- Sender: `0x1f87ae197af539253978d435ad45ccf28fb95024` (`worker`)
- Source: `probes/finalized_callback.py` as it existed at submission time
- Submitted transaction: `0xb2009df95d75eecf5c6b29900c45f0fc02d360d57a16ac68b4c4cb9600172d59`
- Receipt state observed: `COMMITTING` (numeric status `3`)
- Contract address returned by the receipt: `0xeBfF8F00770Bb1576b519858BB87005f1Fb0E2F7`
- Execution result: `FINISHED_WITH_ERROR`
- Trace error: `runner py-genlayer:5jycge4q8k23462jtb0b9fyey1s9qz928sz2nbrd9mg4sxqg2qng not found`

Interpretation: this is not a successful deployment. The address is a ghost
address created by the asynchronous deployment flow; the contract code did
not execute with the selected runner. The source was changed to Bradbury’s
documented `1jb45...` runner only after this canary. A new deployment and a
successful final receipt are required before claiming live COMMIT compatibility.

## Corrected legacy-runner deployment canary

- Network: GenLayer Bradbury Testnet
- Chain ID: `4221`
- RPC: `https://rpc-bradbury.genlayer.com`
- Sender: `0x1f87Ae197af539253978d435aD45cCf28Fb95024` (`worker`)
- Source: `probes/finalized_callback.py` with documented runner `1jb45...`
- GenLayer transaction: `0x86c76b7dd80b64f9582ee1372f4a1386a6c2161d87bc7bd18c739eba0ce59df7`
- Contract address reported by the receipt: `0xbb9D0E807521bf5412F1eb2f76e0E35589B4d037`
- Receipt observed: `COMMITTING` (numeric status `3`)
- Execution observed: `NOT_VOTED` (`txExecutionResult: 0`)
- Created timestamp: `1789003063`
- Round-0 trace: `result_code: 0`, empty stdout/stderr
- Bradbury code lookup at this observation: `contract code not found at address ...` (the receipt was not final)

Interpretation: this corrected submission passed outer transaction admission and
entered Bradbury consensus without the earlier `runner ... not found` error.
Its round-0 leader trace completed successfully, but the receipt is still
`COMMITTING`, the consensus result is not yet voted, and final code lookup is
not available. Do not use the reported address as a live COMMIT endpoint until
a later receipt proves successful execution and finality.

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
- Latest bounded receipt check: `COMMITTING`, with execution error recorded above
- Contract address: `0xeBfF8F00770Bb1576b519858BB87005f1Fb0E2F7` (ghost address only; not a valid deployment)

This is a canary submission only. It does not establish deployment success, finalized self-message delivery, callback state mutation, or COMMIT custody safety. Do not cite it as a successful live demo until the receipt, deployed address, source identity, callback transaction, finality, and state are independently checked.

The worker balance was `10.611703293728233196 GEN` before submission and `10.611306336209951396 GEN` after the bounded receipt check. The difference is recorded as an observed balance change, not as a final fee accounting statement.
