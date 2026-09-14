# Current architecture

COMMIT separates economic state from deterministic evidence utilities while keeping one explicit custody boundary.

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

Its public surface remains 41 methods.

### `CommitHelper`

`contracts/commit_helper.py` is a stateless, synchronous, view-only helper.

It has:

- no storage declarations;
- no public write methods;
- no nondeterministic operations;
- no `gl.message` dependency;
- no nested cross-contract calls;
- no message emission;
- no value transfer.

It performs deterministic URL validation, canonical root/hash derivation, bounded evidence parsing, evidence/snapshot binding checks, decision derivation from validator-agreed raw responses, and read-model formatting.

## Evaluation flow

For each registered evidence record, in mission order:

1. the coordinator performs the web read inside GenLayer nondeterminism;
2. leader and validators agree on the exact raw response representation;
3. execution returns to deterministic coordinator code;
4. the helper validates and interprets that agreed response;
5. a repairable failure is persisted immediately and later evidence is not fetched;
6. only a fully valid evidence set can produce a consequential `COMMIT` or `ABORT` decision.

The helper never participates inside the nondeterministic block.

## Consequence binding

A consequential decision is bound to:

- mission ID and mission version;
- objective and policy digest;
- intent digest;
- sealed effect root;
- sealed evidence root;
- active evaluation evidence root;
- exact decision and reason;
- decision nonce.

Decision application is finality-gated and idempotent.

## Evidence trust model

Evidence registration binds:

- authority ID and immutable authority version;
- authenticated issuer address;
- approved HTTPS host and path prefix;
- stable record ID and record version;
- mission ID and mission version;
- publication and expiry timestamps;
- expected payload hash and snapshot fields.

Sealing requires independent authenticated issuers rather than duplicate labels for the same authority.

## Repair model

Acquisition/integrity failures are persisted as `REPAIR_REQUIRED` rather than silently converted into a semantic negative outcome. Before recovery expiry, an authenticated strictly newer successor for the same bound record identity can replace only the active evaluation evidence while the original sealed root remains immutable.

## Settlement safety

- allocation occurs only through a finalized self-message;
- COMMIT/ABORT application is single-use;
- recovery deadlines prevent indefinite locking;
- claimable rights are consumed before native-value dispatch;
- external delivery is not treated as synchronously reversible.

## Source identities

Certified checkpoint `c152ec75d935a4cb5cf37e2f31aaae89c1bdc525`:

- coordinator SHA-256: `e88d1d78ee8f2d373124bbfbc3f0c8d946385a3250fc028f5956fd74762f8c69`
- coordinator bytes: `19598`
- helper SHA-256: `0120b74e0988f2444c3cc824bd40633c472348da9e1d3fd851c4d7380ffbe632`
- helper bytes: `9394`
