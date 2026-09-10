# Canonical Product Thesis

Status: **FROZEN for implementation**
Date: 2026-09-09

## Name

The protocol name and public brand are **COMMIT**.

## Invention

COMMIT introduces **decentralized semantic atomicity**: a protocol-level method for deciding whether a multi-party autonomous mission has become true as a whole, then atomically allocating its escrowed economic consequences.

## Problem

Autonomous agents can negotiate and execute separate steps, but ordinary transaction systems cannot decide whether the combined outcome satisfies a human or organizational intention expressed in natural language. Partial success can create economic damage: payment without complete delivery, incompatible reservations, stale evidence, substituted obligations, or effects that satisfy individual steps while violating the mission as a whole.

## Why GenLayer is necessary

The acceptance predicate may depend on ambiguous, changing, independently sourced real-world evidence. Deterministic code can validate hashes, identities, deadlines, balances, and state transitions, but it cannot generally decide questions such as:

> Does this complete procurement package satisfy the buyer's stated requirements and constraints?

COMMIT uses deterministic contract logic for custody and invariants, and GenLayer's decentralized AI consensus for the bounded semantic decision. A centralized model response is not authoritative.

## Reference application

Autonomous procurement is the proof, not the protocol boundary. A buyer defines a mission; suppliers prepare commitments; evidence is authority-bound; validators assess the complete package; COMMIT issues a commit or abort decision; escrowed settlement rights are allocated accordingly.

## Protocol objects

- Mission
- Mission Version
- Participant and Role Registry
- Effect Graph
- Prepared Effect
- Prepare Receipt
- Evidence Manifest and Evidence Root
- Semantic Acceptance Predicate
- Semantic Decision
- Commit Certificate
- Abort Certificate
- Compensation Plan
- Claimable Settlement Right
- Mission Receipt

## Non-negotiable properties

- Exact consequence binding
- Mission-version binding
- Participant authorization
- Delegation attenuation
- No replay
- Evidence provenance and freshness
- Deterministic effect hashing
- Deadline recovery
- Single terminal outcome
- Finality-gated irreversible effects
- Idempotent claims and adapters
- No hidden administrative override
- Complete audit trail

## Explicit non-claims

COMMIT does not claim:

- synchronous return values from GenLayer child messages;
- automatic refund when a value-bearing child message fails;
- atomic rollback of arbitrary websites, APIs, chains, or physical-world effects;
- that an accepted but non-final transaction is irreversible;
- that one validator or one LLM response proves mission success;
- that external evidence is trustworthy without authority and freshness validation.

## Success criterion

The protocol succeeds only if an adversarial reviewer can reproduce the full lifecycle, inspect every authoritative transition, verify the source deployed on the target network, and observe that no asset can be allocated outside the declared commit/abort rules.
