# Verification record

Updated: 2026-09-14.

This record separates local/source certification from the historical live Studio Dev proof.

## Certified source checkpoint

Commit:

`c152ec75d935a4cb5cf37e2f31aaae89c1bdc525`

Source identities:

- coordinator: `contracts/commit.py`
- coordinator SHA-256: `e88d1d78ee8f2d373124bbfbc3f0c8d946385a3250fc028f5956fd74762f8c69`
- helper: `contracts/commit_helper.py`
- helper SHA-256: `0120b74e0988f2444c3cc824bd40633c472348da9e1d3fd851c4d7380ffbe632`

## Static validation

Both contracts passed the pinned GenVM validation stack:

- typecheck: pass
- lint: pass
- contract validation: pass
- coordinator public methods: 41
- helper public methods: 8 view / 0 write
- public ABI parity: pass
- helper stateless/view-only guard: pass

## Runtime verification

The certified checkpoint passed:

- targeted multi-contract helper/coordinator smoke: **1 passed**
- semantic regression file: **70 passed**
- full Direct Runtime suite: **113 passed**
- repository regression suite: **433 passed + 334 subtests**

The Direct Runtime uses the verified GenVM archive:

`bd30580f911338d5533460eca8ed714dec371de5803c04e41dbb96430aea7b6e`

## Deployment-envelope verification

The exact coordinator/helper deployment payloads were encoded with `genlayer-js 1.1.8` and checked read-only against the GenLayer RPC environment used during certification.

Both helper and coordinator:

- decoded constructor calldata successfully;
- had matching estimates across both checked RPC surfaces;
- executed under the observed per-transaction gas ceiling in read-only calls.

No blockchain transaction was submitted as part of that qualification.

## Live behavior proof

The historical source-matched v0.7 Studio Dev deployment independently proves both semantic branches:

- mission 008: finalized `COMMIT`, allocation, one-time claim consumption;
- mission 009: finalized `ABORT`, refund allocation, one-time refund consumption.

See [`DEPLOYMENT_LOG_STUDIO_DEV.md`](./DEPLOYMENT_LOG_STUDIO_DEV.md).

## Reproduction

Python:

```sh
uv sync --frozen
uv run python -m pytest -q
```

Frontend:

```sh
npm ci
npm run typecheck
npm run test
npm run build
```

The source/test code in the Agent Tank cleanup branch is intentionally byte-identical to the certified checkpoint. Repository cleanup changes presentation/documentation only.
