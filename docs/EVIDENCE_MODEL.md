# Evidence and Consensus Model

Status: structural authority/path enforcement, snapshot binding, bounded
remote input, v2 schema checks, and full decision-envelope comparison are
implemented and locally tested in revision `0.7.0-reviewable-manifest`. The
source-matched Studio Dev deployment proves both the live COMMIT and ABORT
semantic paths with independent remote records. The new
`get_mission_manifest` read exposes the frozen mission terms, exact ordered
effect/evidence inputs, sealed roots, current decision/allocation state, and
registered authority metadata for reviewer inspection in one bounded response.
Live redirect provenance and cryptographic binding between a registered
GenLayer issuer account and an external real-world organizational identity
remain open. Transaction-level issuer authentication is implemented for
on-chain attestations.

## Authority

The contract owner registers a unique immutable authority ID with a lowercase
HTTPS host, canonical path prefix, one exact GenLayer issuer account address,
and a positive authority version. The authority ID cannot be rewritten or
reactivated after deactivation. A new issuer identity or authority version must
therefore use a new authority ID.

The approved issuer authenticates an evidence attestation by submitting the
attestation transaction itself. The contract requires
`gl.message.sender_address` to equal the registered issuer address and binds
the authority/version, stable record ID/version, mission/version, immutable
URL, exact record hash, publication timestamp, and expiry. The mission
principal can attach only an existing authenticated attestation.

Host labels remain ASCII DNS-style labels (1–63 characters, letters, digits,
and internal hyphens); path prefixes are canonical and do not end in a slash
except for `/`. The registry rejects userinfo, ports, queries, fragments,
percent-encoding, backslashes, dot traversal, empty non-root path segments,
and unsupported schemes. Deactivation blocks new attestations without
rewriting previously stored evidence.

Corroboration requires distinct authenticated issuer addresses, not merely
different authority labels or origins. This authenticates control of the
registered GenLayer account address; it does not by itself prove ownership of
a DNS name, honesty of an organization, or independence between real-world
organizations.

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
origin after redirects. No external-content signature verifier has been added. The implemented
authentication proves that the attestation transaction came from the exact
registered GenLayer issuer address. A future external-signature route, if
required, must verify the precise canonical record with an explicitly trusted
issuer key and version plus the consequential mission/effect bindings and
expiry. A non-empty signature string or self-generated digest is not
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
