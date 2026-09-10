# Verification Policy

COMMIT uses evidence tiers. A claim may move upward only when its required evidence exists.

| Label | Meaning |
|---|---|
| Designed | Written specification exists; no implementation claim |
| Implemented | Source exists and passes static checks |
| Locally tested | Reproducible deterministic tests pass |
| Consensus tested | Multi-validator execution passes with expected receipt and traces |
| Deployed | Address and source hash are recorded for a named network |
| On-chain verified | Deployed source matches, lifecycle receipts succeed, and state/output assertions pass |
| Submission ready | Documentation, demo path, threat model, limitations, deployment evidence, and clean repository have been independently rechecked |

## Rules

1. Never use “perfect,” “flawless,” “fully secure,” or “100%” as an engineering result.
2. Never treat transaction submission, a hash, or `ACCEPTED` alone as execution success.
3. Never hide a timeout, validator disagreement, appeal, revert, stale read, or fee failure.
4. Every network-dependent fact is rechecked on the day it is used.
5. Every deployed artifact records network, chain ID, address, transaction ID, source digest, runtime dependency, tool versions, fee profile, and final execution state.
6. Negative and adversarial tests are required, including replay, stale evidence, unauthorized roles, altered effect graphs, deadline races, duplicate claims, compensation failure, and validator disagreement.
7. Frontend development starts only after the contract/backend gate is explicitly passed and announced to the user.
