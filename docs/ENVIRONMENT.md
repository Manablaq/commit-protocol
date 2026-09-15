# Submission environment

This file records only the environments relevant to the Agent Tank submission.

## Required current deployment target

For Agent Tank, the current-source deployment target is **Studio Next**:

- RPC: `https://studio-next.genlayer.com/api`
- Chain ID: `61997`
- Explorer: `https://explorer-studio-dev.genlayer.com/`

The current coordinator/helper source is not yet successfully deployed there.
The exact current blocker and nonce-safe diagnostic record are in
[`STUDIO_NEXT_CHECKPOINT_2026-09-15.md`](./STUDIO_NEXT_CHECKPOINT_2026-09-15.md).

## Historical live proof environment

COMMIT's historical source-matched end-to-end proof is on GenLayer Studio Dev:

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

The project is being prepared specifically for Agent Tank. The current-source
submission target is Studio Next. Historical Studio Dev v0.7 behavior proof is
preserved as evidence, but it is not represented as the current-source Studio
Next deployment.
