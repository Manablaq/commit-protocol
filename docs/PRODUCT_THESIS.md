# Canonical Product Thesis

Status: **implemented reference scope**
Date: 2026-09-16

## Name

The protocol name and public brand are **COMMIT**.

## Invention

COMMIT introduces **decentralized semantic atomicity**: a protocol-level method
for freezing a mission's economic intent and authoritative evidence, reaching a
decentralized decision over external facts, and allocating escrowed economic
consequences only when that exact decision reaches the required finality.

## Problem

Autonomous workflows cross suppliers, APIs, evidence sources, deadlines, and
payment boundaries. Partial success can create economic damage: payment without
complete delivery, stale evidence, substituted obligations, or settlement
against facts that were never bound to the original mission.

## Why GenLayer is necessary

Ordinary deterministic contracts cannot fetch changing external web evidence
and obtain decentralized validator agreement over that nondeterministic input.

The implemented Agent Tank reference scope uses GenLayer validators to fetch
authority-bound evidence and reach agreement over the consequential evidence
result. Deterministic COMMIT logic then enforces the policy, roots, deadlines,
finality, and settlement consequence.

**The current reference implementation does not use LLM inference.** It does
not claim that an arbitrary natural-language objective is interpreted by an AI
model. Its implemented semantic predicate is deliberately bounded and
structured. Future policy modules may use GenLayer AI/comparative primitives,
but those are outside the claims of this submission.

## Reference application

Autonomous procurement is the proof, not the protocol boundary. A principal
defines a mission; authorized suppliers prepare effects; authenticated issuers
attest versioned evidence; validators evaluate the bounded external records;
COMMIT derives COMMIT or ABORT; and finalized deterministic logic allocates the
precommitted settlement rights.

## Non-negotiable properties

- exact consequence binding;
- mission/version binding;
- participant authorization;
- no replay or double allocation;
- authenticated evidence provenance;
- immutable record/version identity;
- freshness, future-time rejection, and expiry;
- distinct-issuer corroboration;
- deterministic effect/evidence hashing;
- repairable evidence acquisition failures;
- deadline recovery;
- single terminal economic outcome;
- finality-gated allocation;
- one-time claim consumption;
- no hidden administrative outcome override;
- reproducible audit evidence.

## Explicit non-claims

COMMIT does not claim:

- arbitrary natural-language understanding in the current reference policy;
- synchronous rollback of websites, APIs, chains, or physical actions;
- automatic authenticated proof of downstream native-value delivery;
- that distinct blockchain addresses prove independent real-world companies;
- that an accepted but non-final transaction is irreversible;
- that consensus status alone proves successful execution.

## Success criterion

The submission succeeds only if a reviewer can reproduce the implemented
lifecycle, inspect every authoritative transition, verify the exact deployed
source on the target environment, distinguish finality from execution success,
and observe that protocol-held settlement rights cannot be allocated outside
the declared COMMIT/ABORT rules.
