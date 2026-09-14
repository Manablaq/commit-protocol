# COMMIT Bradbury-native v0.9 architecture

This candidate preserves the COMMIT public method surface and reviewer-hard-gate semantics while changing only the internal deployment architecture needed to fit Bradbury's observed outer-transaction envelope.

## Frozen parent

- parent commit: `258b1db312be3ee4b640986f7544a0b8321e5201`
- parent contract SHA-256: `a298b2697846adbcddf88272a0fbd514778a7fee733fa8b6d6fa489ee973e33b`
- parent source bytes: `48589`
- measured exact parent deployment `eth_call` minimum: `38548235`
- observed live per-transaction admission cap: `16777216`

No parent deployment reached GenLayer consensus, so there is no live contract state to migrate.

## v0.9 split

The economic/state coordinator remains `contracts/commit.py`. It is the only component allowed to:

- hold mission state and claimable balances;
- accept mission funding;
- persist evidence failure/repair state;
- execute nondeterministic web reads and exact validator agreement;
- create the finalized self-message for `apply_decision`;
- allocate COMMIT/ABORT entitlements;
- consume claims and emit native transfers.

`contracts/commit_helper.py` is an immutable constructor-bound, stateless, synchronous view helper. It has no storage declarations, no write methods, no nondeterministic operations, no message emission, and no value transfer. It performs deterministic URL validation, hash/root derivation, evidence parsing/binding/hash checks, decision derivation from validator-agreed response bytes, and read-model formatting.

The coordinator calls the helper only outside nondeterministic blocks. For each evidence record in mission order, the coordinator first reaches leader/validator agreement on that record's exact raw response bytes, then performs deterministic helper validation before fetching the next record. A repairable failure therefore preserves the frozen R3 first-failing-source short-circuit and no later source is fetched after that failure.

## Source identities

- coordinator bytes: `19598`
- coordinator SHA-256: `e88d1d78ee8f2d373124bbfbc3f0c8d946385a3250fc028f5956fd74762f8c69`
- helper bytes: `9394`
- helper SHA-256: `0120b74e0988f2444c3cc824bd40633c472348da9e1d3fd851c4d7380ffbe632`

The previously measured `20185`-byte synthetic source point is a conservative, empirical estimator boundary at one pinned Bradbury block. It is **not** claimed to be an official protocol source-size maximum. Final v0.9 qualification additionally requires read-only Bradbury `eth_call` gas-floor checks for both exact deployment payloads.

## Safety invariants

The public 41-method coordinator API remains frozen. Protocol/revision strings, policy digest/rule, evidence schema, root/hash framing, decision nonce framing, repairable evidence behavior, recovery deadline behavior, finalized allocation callback, and consume-before-transfer withdrawal behavior remain reviewer hard gates.

Any change to either coordinator or helper source invalidates the fee/profile identity.
