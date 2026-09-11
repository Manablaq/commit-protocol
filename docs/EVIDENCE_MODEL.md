# Evidence and Consensus Model

Status: structural authority/path enforcement, snapshot binding, bounded
remote input, v2 schema checks, and full decision-envelope comparison are
implemented and locally tested in revision `0.7.0-reviewable-manifest`. The
source-matched Studio Dev deployment proves both the live COMMIT and ABORT
semantic paths with independent remote records. The new
`get_mission_manifest` read exposes the frozen mission terms, exact ordered
effect/evidence inputs, sealed roots, current decision/allocation state, and
registered authority metadata for reviewer inspection in one bounded response.
Live
redirect provenance and issuer cryptographic authentication remain open.

## Authority

The contract owner registers a unique authority ID with a lowercase HTTPS host
and path prefix. Host labels are ASCII DNS-style labels (1–63 characters,
letters, digits, and internal hyphens); path prefixes are canonical and do not
end in a slash except for `/`. The registry rejects userinfo, ports, queries,
fragments, percent-encoding, backslashes, dot traversal, empty non-root path
segments, and unsupported schemes. Evidence registration requires an active
authority and an exact origin/path boundary match. Deactivation blocks new
evidence without rewriting stored history.

This is structural allowlisting, not proof that the owner controls the DNS
name, that the publisher is honest, or that two registered origins represent
two independent organizations. Sealing requires two distinct registered
origin/path pairs; two labels for the same origin cannot satisfy corroboration.
The contract still does not cryptographically establish organizational
independence.

## Evidence v2

Every fetched record must use `commit-evidence-v2` and include the exact:

- mission ID and objective;
- `all-evidence-and-effects-v1` policy rule and its registered digest;
- mission intent digest and sealed effect root;
- evidence ID, authority ID, URL, subject, and expiry;
- payload hash matching canonical JSON;
- boolean mission eligibility and a boolean claim for every sealed effect.

The evaluator independently re-fetches each source. COMMIT is possible only
when all records and all effect claims are eligible. The leader and validator
must agree on the decision, reason, revision, mission, intent, policy, policy
rule, effect root, evidence root, and both manifest counts. The remote body is capped
at 16 KiB and reason codes are capped at 128 printable characters. The parser
rejects duplicate object keys, non-standard numeric constants such as `NaN`,
and unknown top-level fields so every validator sees one strict record shape.
Validator equivalence includes the decision and every sealed snapshot binding
field, so a well-formed leader cannot substitute another mission, policy, root,
or manifest size. `get_mission_receipt` exposes those commitments together with
the frozen objective, principal, budget, deadlines, decision nonce, and
allocation state. `get_mission_manifest` exposes the bounded root inputs and the
authority record used for each evidence URL, so a reviewer can reconstruct what
was sealed without relying on an off-chain database.

## Remaining provenance boundary

The inspected GenLayer fetch response exposes status, headers, and body but
does not expose a verified final URL in the current local proof. The contract
therefore cannot claim that a successful response remained on the registered
origin after redirects. No signature verifier has been added. A future
cryptographic route must verify the precise canonical record with a registered
issuer public key, including key version, subject, mission/effect binding,
nonce, and expiry. A non-empty signature string or self-generated digest is not
authentication.

## Failure and freshness

Unavailable publishers, malformed content, schema mismatch, snapshot mismatch,
digest mismatch, stale evidence, or missing authority proof prevent a decision
from being applied. They do not silently become a semantic ABORT; a failed
evaluation leaves the sealed mission recoverable until its recovery deadline.
Evaluation is permissionless after sealing, so authority deactivation cannot
strand a sealed mission by disabling its principal's evaluation call.

The timestamp is transaction-pinned. Evidence expiry through the recovery
boundary prevents an obviously stale registration but cannot guarantee that a
physical reservation still exists when finality completes.
