# Studio Next deployment checkpoint — 2026-09-15

This document records the exact COMMIT deployment/readiness state reached on
2026-09-15. It separates historical live behavior proof from the current
Agent Tank deployment target and does not claim a successful current-source
deployment where none exists.

## Canonical current target

- Network: **Studio Next**
- RPC: `https://studio-next.genlayer.com/api`
- Chain ID: `61997`
- Explorer: `https://explorer-studio-dev.genlayer.com/`
- Worker: `0x1f87Ae197af539253978d435aD45cCf28Fb95024`

For the Agent Tank submission, the current-source deployment target is Studio
Next. The historical Studio Dev v0.7 deployment remains behavior evidence only.

## Repository/source identity at this checkpoint

Repository `main` before this documentation update:

`b02be2978d23b9aebd2c75f87e14c2078aeb5fb4`

Current contract source identities:

- coordinator: `contracts/commit.py`
- coordinator SHA-256:
  `e88d1d78ee8f2d373124bbfbc3f0c8d946385a3250fc028f5956fd74762f8c69`
- helper: `contracts/commit_helper.py`
- helper SHA-256:
  `0120b74e0988f2444c3cc824bd40633c472348da9e1d3fd851c4d7380ffbe632`

Commit `b02be297...` is a documentation/submission-preparation commit on top of
the certified source checkpoint
`c152ec75d935a4cb5cf37e2f31aaae89c1bdc525`; the contract source bytes are
unchanged.

The certified source passed:

- GenVM typecheck/lint/validation for coordinator and helper;
- coordinator public ABI parity: 41 methods;
- helper stateless/view-only guards;
- semantic regression: 70 passed;
- Direct Runtime: 113 passed;
- repository regression: 433 passed + 334 subtests.

## Historical live proof — not the current-source deployment

A source-matched v0.7 deployment already proves both semantic branches on
Studio Dev:

- contract: `0x10c708517b4465596E2dc40De92B30A610Cb7a10`
- deployment transaction:
  `0x03071d2f8353c993a6a8aae38c1086e025df712f320090fd036ace2ef218ccab`
- result: `FINALIZED`, `FINISHED_WITH_RETURN`
- source SHA-256:
  `4dd61b7e7a5acbdc254f7a63419fe7b4a2674909d49fa07e0d0b051fd74eb36f`
- mission 008: finalized `COMMIT` path and one-time claim consumption;
- mission 009: finalized `ABORT` path and one-time refund consumption.

See [`DEPLOYMENT_LOG_STUDIO_DEV.md`](./DEPLOYMENT_LOG_STUDIO_DEV.md).

## Prior current-source helper write attempt

A previously authorized single helper profiling deployment was submitted once
and is retained only as failure evidence:

- transaction:
  `0xc46c44653cecb443f7276430a9a314e0fb0a567c74136b9356cd859b2183b604`
- nonce movement: `66 -> 67`
- execution result: `FINISHED_WITH_ERROR`
- validator execution error: `invalid_contract runner malformed`
- no successful helper contract address exists from this attempt.

That authorization is consumed. It does not authorize any retry, coordinator
deployment, mission write, or frontend change.

## Zero-write Studio Next certification

A read-only certification was run against the exact Studio Next RPC.

### RPC and chain

- `eth_chainId` returned `0xf22d` = `61997`;
- Studio Next RPC reachable: yes;
- worker pending nonce before: `67`.

### Live fee policy

The Studio Next fee policy RPC succeeded and reported fees enabled. Observed
values:

- `genPerTimeUnit = 1`
- `storageUnitPrice = 250000000`
- `receiptGasPrice = 250000000`
- `timeUnitOverlayBps = 1500`
- `messageFeeParamsBudgetFloor = 76548000000000`
- `genvmStartBudgetFloor = 127878000000000`

### Official control and exact COMMIT helper probes

The read-only schema probe used the exact public Studio control from GenLayer
Studio commit `c94072951e483510329670aa427fba3fa6944f45`:

- `examples/contracts/storage.py`
- control SHA-256:
  `c19ffb3e0c623705639dcb4f33a507cefb918655e7943cc8bf8f0d649282fb4b`

At that earlier checkpoint both the official control and the exact COMMIT helper
returned:

- GenVM: `v0.3.0-rc7-x86_64-linux-release`
- `compiled_modules = 0`
- `invalid_contract runner malformed`

Classification at that checkpoint:

```text
STUDIO_NEXT_RPC=HEALTHY
STUDIO_NEXT_FEES=HEALTHY
OFFICIAL_CONTROL=RUNNER_MALFORMED
COMMIT_HELPER=RUNNER_MALFORMED
REDEPLOYMENT_ALLOWED=NO
```

No transaction was submitted and the pending nonce remained `67`.

The locally preserved certification directory is:

`/Users/mralbert/Downloads/commit-studio-next-certification-20260915T015244Z`

Key preserved response hashes:

- official-control response SHA-256:
  `e1b079204539a12c8e2438fb643819eb385c5ffef5a0ed98c2e7879e4fe8abf5`
- COMMIT-helper response SHA-256:
  `b9c57773d939ee85441d1562ac529f986c3d3a756140a73f4cf942ad854df4e2`
- nonce-before/nonce-after JSON SHA-256:
  `1f41d05c9e391e522fa1f40551c15ebf78fe2d1c6c8a5eb95306935b8dac9f91`

The raw local artifacts are not reconstructed or fabricated by this repository
checkpoint.

## Later hosted Studio UI diagnostic

A later manual diagnostic was performed in the hosted Studio UI at
`https://studio-dev.genlayer.com/contracts` using Studio's `storage.py`
example.

Observed behavior:

- the UI successfully parsed the contract schema;
- the constructor field `initial_storage` was recognized and rendered;
- entering `test` was accepted;
- the hosted example showed runner
  `py-genlayer:5jycge4q8k23462jtb0b9fyey1s9qz928sz2nbrd9mg4sxqg2qng`;
- clicking Deploy did **not** produce a transaction;
- the UI failed during `sim_estimateTransactionFees`;
- JSON-RPC code: `-32000`;
- message: `execution failed`;
- the traceback reached Studio's `_gen_call_with_validator` simulation path;
- Studio rejected the simulation because the simulated receipt did not report
  successful execution;
- the worker pending nonce was rechecked against the Studio Next RPC and
  remained `67`.

Current safe interpretation:

```text
STUDIO_NEXT_REACHABLE=YES
CHAIN_ID_61997=YES
FEE_POLICY_RPC=PASS
HOSTED_UI_SCHEMA_PARSE=PASS
HOSTED_UI_CONSTRUCTOR_PARSE=PASS
SIMULATED_DEPLOY_EXECUTION=FAIL
ACTUAL_DEPLOYMENT_TX_SUBMITTED=NO
PENDING_NONCE=67
CURRENT_SOURCE_DEPLOYED_ON_STUDIO_NEXT=NO
```

The later UI behavior is an improvement over the earlier schema failure, but it
is **not** a deployment success. The blocker has narrowed to unsuccessful
simulated GenVM deployment execution.

## Current decision

Do not alter COMMIT contract source merely to work around this hosted-runtime
symptom, and do not spend another deployment transaction while the simple
Studio control cannot complete deployment simulation successfully.

No evidence currently establishes a COMMIT source defect. The current source
remains locally/runtime certified and unchanged.

## Next required gate

Before any new write:

1. capture the underlying GenVM receipt/log for the failed
   `sim_estimateTransactionFees` control simulation;
2. require the simple Studio control deployment simulation to succeed;
3. rerun the exact Studio Next read-only control/helper gate;
4. require both the control and exact COMMIT helper to pass;
5. re-read the live Studio Next fee policy;
6. verify worker balance and nonce;
7. generate a fresh source-bound helper deployment fee envelope against
   Studio Next;
8. freeze the exact helper deployment envelope;
9. obtain a new explicit authorization for exactly one helper deployment;
10. submit once and require `FINALIZED` + `FINISHED_WITH_RETURN`.

Only after a successful helper deployment should the coordinator envelope,
coordinator deployment, and fresh COMMIT/ABORT lifecycle proofs be prepared.

## Public app/frontend status

- stable public URL: `https://commitprotocol-genlayer.vercel.app`
- this checkpoint does not change the Vercel project or public URL;
- this checkpoint does not change contract source;
- this checkpoint does not change frontend source.
