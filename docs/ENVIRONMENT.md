# Verified Environment Baseline

Status: **Phase 2 partially closed: Bradbury-compatible source path locally verified; live deployment still unproven**
Verified: 2026-09-10

## Protocol family

The current development-preview documentation describes the Consensus/Node v0.6 release-candidate family. The matching public prereleases were verified directly against npm and PyPI:

| Component | Verified candidate | Registry evidence |
|---|---:|---|
| GenLayer CLI | `0.40.0-rc.3` | npm `genlayer` dist-tag `rc` |
| JavaScript SDK | `2.0.0-rc.1` | npm `genlayer-js` dist-tag `rc` |
| Python SDK | `0.19.0rc2` | PyPI `genlayer-py` |
| Test suite / gltest | `0.30.0rc2` | PyPI `genlayer-test` |
| GenVM linter | `0.11.1rc2` | PyPI `genvm-linter` |

The installed global CLI was rechecked at `0.39.1`; it is **not** the selected COMMIT toolchain. COMMIT will use project-isolated tooling so existing projects remain untouched.

## Network baseline

The current official network table distinguishes the production-like Bradbury testnet from the temporary Studio development preview:

### Bradbury target

- Alias: `testnet-bradbury`
- GenLayer RPC: `https://rpc-bradbury.genlayer.com`
- Chain ID: `4221`
- Consensus main contract: `0x0112Bf6e83497965A5fdD6Dad1E447a6E004271D`
- Explorer: `https://explorer-bradbury.genlayer.com/`
- Read-only CLI check on 2026-09-10: `genlayer network info` reported the values above.

### Studio development preview

- Canonical RPC: `https://studio-dev.genlayer.com/api`
- Chain ID: `61997`
- Read-only RPC check on 2026-09-09: `eth_chainId` returned `0xf22d` (`61997`).
- This environment is temporary and may reset; it is not Bradbury.

COMMIT must not reuse preview addresses, fee assumptions, or runtime conclusions on Bradbury. Before Bradbury deployment, the implementation must verify network schema, consensus version, transaction format, fee support, and a minimal canary contract against Bradbury.

## Unresolved before dependency lock

- Transaction Kit source is resolved, but its compatibility remains untested (see below).
- GenVM runtime dependency hash appropriate for the selected preview
- Whether Agent Tank judging requires a specific network rather than a reproducible preview deployment

Unresolved production choices block custody implementation. The isolated probe harness pins the verified Python packages in `pyproject.toml` and all resolved dependencies in `uv.lock`; this does not establish compatibility with the live network. The probe runtime header is taken from a checksum-verified release archive.

## Transaction Kit investigation

The [official integration instructions](https://docs.genlayer.com/developers/decentralized-applications/transaction-kit-integration) use `github:genlayerlabs/genlayer-transaction-kit#pkg/core` before registry publication. The branch resolved on 2026-09-09 to `7a32d40a3e0c1d9962491b7e78423e2b969848ef`.

Its [manifest at that commit](https://github.com/genlayerlabs/genlayer-transaction-kit/blob/7a32d40a3e0c1d9962491b7e78423e2b969848ef/package.json) declares `@genlayer/transaction-kit` version `0.1.0`, Node `>=18.6.0`, and a floating `genlayer-js#v2-dev` dependency. This is evidence of package location, not evidence of a compatible locked stack. A later SDK integration must resolve and test that dependency explicitly. The kit is not needed for the protocol specification.

## Corrections to the initial progress report

Phase 2 was previously described as completed too early. Published package versions and documented network settings do not verify the deployed Studio/consensus versions, runtime hash, hackathon network requirement, or withdrawal failure semantics. Those remain open. Conceptual specification may proceed, but no fund-bearing implementation or deployment gate has passed.

The public hackathon page initially returned no readable rules through text retrieval. Subsequent browser inspection on 2026-09-09 resolved this: the actual submission form supports Studio, Bradbury or Asimov address links, requires a website, and requires a public repository belonging to the linked GitHub account. No exclusive Bradbury requirement appears. The reference track is Agentic Commerce Infrastructure. Source: https://portal.genlayer.foundation/agent-tank/hackathon/submit

## Isolated probe runtime and Bradbury compatibility

- Host interpreter: Python 3.12.14 (the test suite requires Python >=3.12).
- GenVM manager release: `v0.6.0-rc4`, published 2026-09-09.
- Archive: `genvm-universal.tar.xz`.
- Published and locally verified SHA-256: `bd30580f911338d5533460eca8ed714dec371de5803c04e41dbb96430aea7b6e`.
- The first local probe used the current v0.6 runner `py-genlayer:5jycge4q8k23462jtb0b9fyey1s9qz928sz2nbrd9mg4sxqg2qng`. A bounded Bradbury canary proved that runner is not available on Bradbury: the transaction trace returned `runner ...5jyc... not found`.
- Bradbury’s documented first-contract path specifies `py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6`, the legacy `from genlayer import *` package layout, `gl.Contract`, and `gl.get_contract_at`.
- The same verified manager archive contains the legacy runner and its dependency `py-lib-genlayer-std:11rhn002yfajawsz7fai6mykznbxkxs6l91iskj5cm82c92qhy3v`. COMMIT and its probes now use the documented `1jb45...` header and pass the local legacy-runtime suite.
- The locally installed modern SDK remains useful for tooling and linter checks, but it is not evidence that the v0.6 runner is available on Bradbury. The production source header, package imports, message API, and consensus primitive must remain aligned with the target runner actually accepted by Bradbury.
- Local legacy-runtime tests require the explicit adapter in `tests/runtime/conftest.py` because the installed `gltest-direct` package targets the newer package layout. This adapter is test infrastructure only; it is not part of the deployed contract.

Release source: https://github.com/genlayerlabs/genvm-manager/releases/tag/v0.6.0-rc4

## Required transaction semantics

- `ACCEPTED` is provisional; irreversible value movement is finality-gated.
- A successful operation must have an acceptable consensus status **and** successful execution (`FINISHED_WITH_RETURN`).
- Internal messages are asynchronous and do not provide synchronous child results.
- External messages execute only after finalization.
- Failed value-bearing child messages do not imply automatic refund.
- User value and protocol fee deposits are separate.
- Fee distributions must be generated from measured profiles and estimated against current network pricing.
- Appeals use the supported high-level appeal flow and current appeal charge.

## Sources

- [Networks](https://docs.genlayer.com/developers/networks)
- [First Intelligent Contract](https://docs.genlayer.com/developers/intelligent-contracts/first-contract)
- [Consensus v0.6 migration](https://docs.genlayer.com/developers/consensus-v06-migration)
- [GenLayerJS](https://docs.genlayer.com/api-references/genlayer-js)
- [GenLayerPY](https://docs.genlayer.com/api-references/genlayer-py)
- [CLI repository and changelog](https://github.com/genlayerlabs/genlayer-cli)
- [Testing suite](https://github.com/genlayerlabs/genlayer-testing-suite)
