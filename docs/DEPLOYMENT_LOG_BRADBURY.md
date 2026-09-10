# COMMIT Bradbury Deployment Log

Updated: 2026-09-10 (Africa/Lagos)

## Deployment status

The full `contracts/commit.py` deployment has been submitted to the Bradbury
RPC, but its GenLayer transaction receipt and contract address are not yet
available. No deployment is considered successful until the protocol receipt
proves successful execution and the deployed source can be matched to the
local file.

## Full COMMIT deployment attempt

- Network: GenLayer Bradbury Testnet
- Chain ID: `4221`
- RPC: `https://rpc-bradbury.genlayer.com`
- Sender: `0x1f87Ae197af539253978d435aD45cCf28Fb95024` (`worker`)
- Source: `contracts/commit.py`
- Runner: `py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6`
- Outer EVM nonce: `0x2d0`
- Outer EVM transaction observed: `0x0e94d2c86f880da4958f1690545ec62727d1aa40927e1838c29005ace65f8ad3`
- Observation: transaction was pending/not yet mined at the time of the
  bounded RPC check; the GenLayer transaction ID was not yet available
- Action: do not submit a replacement or duplicate deployment until this nonce
  is resolved

## Required proof before using the address

1. Recover the GenLayer transaction ID from the mined outer receipt or CLI
   output.
2. Verify a receipt of `ACCEPTED` or `FINALIZED` with `AGREE` and
   `FINISHED_WITH_RETURN`.
3. Read the deployed code using the Bradbury object-form `gen_getContractCode`
   request and compare its SHA-256 with the local source.
4. Read `protocol_info()` and verify the expected revision and feature flags.
5. Run only bounded, test-funded lifecycle probes before enabling any real
   custody flow.

The accepted zero-value probe at
`0xbb9D0E807521bf5412F1eb2f76e0E35589B4d037` proves the documented legacy
runner path for that probe only. It is not the COMMIT deployment address.
