# Evidence and Consensus Model

Status: design specification. All enforcement and negative tests remain to be implemented.

## Authority

The principal authorizes an immutable publisher policy when sealing. A publisher record binds authority ID, HTTPS origin, allowed path segments, subject scope, and policy version. Authority ownership must be established separately; registration is not proof that a publisher is honest or independent.

URLs are parsed structurally. Exact scheme, normalized host, effective port, and path-segment boundaries are checked. Userinfo, fragments, ambiguous encoded separators, dot traversal, conflicting normalization, and unsupported schemes are rejected. Shared hosting requires account/repository path scope; matching `githubusercontent.com` alone is insufficient. Redirects require enforcement on every hop and final destination. If the GenLayer fetch API cannot establish this, that source pattern is disallowed until a signature-based alternative is verified.

A signature alternative must verify the precise canonical record with the registered public key, including key version, subject, mission/effect binding, nonce, and expiry. A nonempty signature string or self-generated digest is not authentication.

## Freshness and identity

Each record carries stable ID, version, subject, publication timestamp, validity interval, and content digest. Validators independently fetch original records, reject digest mismatches, and enforce the mission's evidence policy. Publication timestamps authenticated by an issuer are issuer assertions; observation timestamps establish only when the protocol observed a record.

Freshness must specify its reference time. Transaction-time freshness does not imply freshness at physical delivery or finalization. Mutable sources require a pinned version and expiry policy. Multiple URLs under one authority do not constitute independent corroboration.

## Failure and repair

Network failure, unavailable publisher, malformed content, digest mismatch, stale record, or missing authority proof blocks COMMIT. It does not by itself prove the proposed procurement violates the intent. Return a bounded repair reason where execution permits; otherwise leave the previous state intact and retain deterministic timeout recovery.

Repair creates a new snapshot revision and invalidates affected supplier and principal approvals. It cannot modify sealed consequences in place or extend the hard recovery boundary.

## Independent reasoning

Every validator receives the sealed intent and constraints, fetches the authorized evidence, and evaluates the entire assembled outcome. Evidence is untrusted data, including instructions embedded in documents. It cannot change the evaluation rules or trigger tools beyond the configured evidence fetches.

Hard checks precede semantic reasoning: permissions, balances, timestamps, graph integrity, exact recipients, amounts, and receipt binding. The nondeterministic output is a tightly bounded decision and reason code. Consequential fields are constructed and checked deterministically from sealed storage. The validator must reject a wrong leader decision even if the leader output is perfectly formatted.

Documentation source: [GenLayer transaction context](https://docs.genlayer.com/developers/intelligent-contracts/features/transaction-context) establishes the timestamp behavior used in this design. URL rules and authority policies above are COMMIT requirements, not claims that the SDK enforces them automatically.
