# Current architecture

COMMIT separates economic state from deterministic evidence utilities while
keeping one explicit custody boundary.

## Components

### `CommitProtocol`

`contracts/commit.py` is the coordinator and the only component allowed to:

- hold mission state and claimable balances;
- accept mission funding;
- authorize and freeze mission inputs;
- persist evidence failure/repair state;
- execute nondeterministic web reads and validator agreement;
- emit the finalized self-message for decision application;
- allocate COMMIT/ABORT entitlements;
- consume claims and dispatch native value.

The hardening candidate also rejects future-dated evidence, exposes its exact
constructor-bound helper address through `protocol_info`, and requires a claim
transaction's immediate sender and original submitter to be the same address.

### `CommitHelper`

`contracts/commit_helper.py` is a stateless, synchronous, view-only helper. It
has no storage declarations, public write methods, nondeterministic operations,
message emission, or value transfer.

The helper performs deterministic URL validation, canonical root/hash
derivation, bounded evidence parsing, evidence/snapshot binding checks,
decision derivation from validator-agreed raw responses, and read-model
formatting.

## Evaluation flow

For each registered evidence record, in mission order:

1. the coordinator performs the web read inside GenLayer nondeterminism;
2. validators bind the consequential evaluation to the agreed response;
3. execution returns to deterministic coordinator code;
4. the helper validates and interprets the agreed response;
5. a repairable acquisition/integrity failure is persisted immediately;
6. only a fully valid evidence set can produce `COMMIT` or `ABORT`.

Evidence attestation is accepted only when:

- the registered authority and issuer match;
- mission and record versions match;
- the URL is inside the authority's bound HTTPS host/path;
- the exact record hash is bound;
- `published_at` is not before mission creation;
- `published_at` is not later than the current GenLayer transaction time; and
- expiry remains valid through the mission recovery boundary.

## Consequence binding

A consequential decision binds mission/version, objective, policy, intent
digest, frozen effect root, sealed evidence root, active evaluation evidence
root, exact decision/reason, and the decision nonce. Decision application is
finality-gated and idempotent.

## Evidence trust model

Evidence requires an authenticated issuer-address attestation. Distinct issuer
addresses provide structural corroboration, but COMMIT does not claim that two
addresses by themselves prove two independent real-world organizations.

A redirect cannot change the attested record identity or payload digest: the
issuer-bound exact content hash and mission/version binding remain mandatory.

## Settlement boundary

COMMIT guarantees allocation and one-time consumption of protocol-held
settlement rights. Native-value dispatch is an external finalization message
to the GenLayer chain layer. COMMIT does not claim authenticated downstream
delivery/reconciliation beyond the tested external-message boundary.

The direct-claim guard prevents an internal-message chain or relayer from
claiming on behalf of a beneficiary through the public claim method.

## Verification backend

The `/verify` backend reads transaction truth through supported hosted-Studio
transaction/status surfaces and keeps finality distinct from execution success.
The Vercel rewrite passes its current named wildcard as `path` (legacy routes
used `1`). The service removes only those documented transport keys before
enforcing the exact public query allowlist; unknown non-reserved and duplicate
semantic keys still fail closed.

## Candidate source identities

- coordinator SHA-256: `e235731ac223ee136b06b8cfc332065927a03553a3b1f5531571cd4d5da119c6`
- coordinator bytes: `19873`
- helper SHA-256: `dfb564fbd644fae756808fee2afc1f43c35d0dde095e33ad9f4802569e80007a`
- helper bytes: `9428`

These are local hardening-candidate identities. They are not represented as
deployed until a fresh exact-source deployment proof is recorded.
