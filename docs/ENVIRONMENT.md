# Submission environment

This file records only the environments relevant to the Agent Tank submission.

## Live proof environment

COMMIT's live end-to-end proof is on GenLayer Studio Dev:

- RPC: `https://studio-dev.genlayer.com/api`
- Chain ID: `61997`
- Source-matched v0.7 contract: `0x10c708517b4465596E2dc40De92B30A610Cb7a10`
- Deployment result: `FINALIZED`, `FINISHED_WITH_RETURN`

The detailed transaction record is in [`DEPLOYMENT_LOG_STUDIO_DEV.md`](./DEPLOYMENT_LOG_STUDIO_DEV.md).

Studio Dev is a preview environment and may reset. The repository therefore preserves transaction IDs, source hashes, and exact contract addresses for the recorded proof.

## Current source verification environment

The newer repository checkpoint `c152ec75d935a4cb5cf37e2f31aaae89c1bdc525` was certified with:

- Python `3.12`
- `genlayer-py==0.19.0rc2`
- `genlayer-test==0.30.0rc2`
- `genvm-linter==0.11.1rc2`
- isolated Pyright `1.1.408`
- verified GenVM archive SHA-256 `bd30580f911338d5533460eca8ed714dec371de5803c04e41dbb96430aea7b6e`

The current repository source is a later certified checkpoint and is not claimed to be source-identical to the Studio Dev v0.7 deployment.

## Agent Tank scope

The project is being prepared specifically for Agent Tank. No additional network deployment is treated as a submission requirement unless the actual Agent Tank submission form explicitly requires it.
