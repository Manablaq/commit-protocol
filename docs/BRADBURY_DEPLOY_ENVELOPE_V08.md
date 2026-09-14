# Bradbury deployment envelope — COMMIT v0.8

## Proven blocker

The reviewer-ready source at `0ad673eb39bd642614ca6c288aef5be5e17082ee` was
**93083 bytes** with SHA-256
`1872dd0cbf92cc7edfffc4b4ab30f898584cbbf251f9ac32a1553b8b98f54b73`.

The canonical Bradbury attempt failed before submission with
`BlockPubdataLimitReached`. The SDK's later 200,000-gas fallback produced the
secondary `intrinsic gas too low` error. The preserved attempt record contains
no GenLayer transaction hash and no contract address.

## Repair

The deploy artifact is structurally compacted while keeping the readable source
permanently reviewable at `0ad673eb39bd642614ca6c288aef5be5e17082ee`.

The compact source:

- preserves every public method name, decorator, argument name and return type,
- preserves every literal value, evidence/receipt/manifest key and error text,
- preserves all consensus, finality, evidence, liveness and value-transfer logic,
- alpha-renames only internal storage/module-constant/private/local implementation identifiers,
- optionally pools repeated string values without changing their values,
- reverses mechanically to the exact executable AST of the readable source,
- must generate the exact same GenVM public schema,
- must pass the complete top-level and Direct Mode regression suites,
- must remain at or below **49152 bytes (48 KiB)**.

Compact SHA-256: `a298b2697846adbcddf88272a0fbd514778a7fee733fa8b6d6fa489ee973e33b`
Compact bytes: `48589`
Selected transform: `alpha_strings_usererror_module_constants`

The complete deterministic identifier mapping is stored in
`docs/BRADBURY_COMPACT_SOURCE_MAP_V08.json`.
