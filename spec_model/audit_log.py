"""Deterministic append-only publication audit log for COMMIT.

Step 5 links the existing Step-3 run identity and Step-4 artifact identity
into an ordered, hash-linked publication history. It does not define a new
run identity, a new artifact hash, or Step-6 policy metadata.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from spec_model.artifacts import ArtifactError, bundle_digest
from spec_model.canonical import CanonicalError, digest, require_hash


AUDIT_ENTRY_SCHEMA = "commit-review-audit-entry-v1"
AUDIT_ENTRY_OBJECT_TYPE = "review_audit_entry"
GENESIS_PREVIOUS_DIGEST = "0" * 64

_ENTRY_FIELDS = {
    "schema",
    "sequence",
    "previous_digest",
    "published_at",
    "run_id",
    "bundle_digest",
}


class AuditError(ValueError):
    """Raised when an audit entry or audit chain is invalid."""


def _require_hash(value: object, name: str) -> str:
    if type(value) is not str:
        raise AuditError(f"{name} must be lowercase SHA-256 hex")

    try:
        return require_hash(value, name)
    except CanonicalError as exc:
        raise AuditError(str(exc)) from exc


def _require_nonnegative_int(value: object, name: str) -> int:
    if (
        type(value) is not int
        or value < 0
        or value >= 2**256
    ):
        raise AuditError(f"{name} must be a u256 integer")

    return value


def _validate_entry_shape(entry: object) -> dict[str, Any]:
    if type(entry) is not dict:
        raise AuditError("audit entry must be an object")

    if set(entry) != _ENTRY_FIELDS:
        raise AuditError("audit entry fields do not match schema")

    if entry.get("schema") != AUDIT_ENTRY_SCHEMA:
        raise AuditError("invalid audit entry schema")

    _require_nonnegative_int(
        entry.get("sequence"),
        "sequence",
    )

    _require_hash(
        entry.get("previous_digest"),
        "previous_digest",
    )

    _require_nonnegative_int(
        entry.get("published_at"),
        "published_at",
    )

    _require_hash(
        entry.get("run_id"),
        "run_id",
    )

    _require_hash(
        entry.get("bundle_digest"),
        "bundle_digest",
    )

    return entry


def entry_digest(entry: object) -> str:
    """Return the canonical digest of one validated audit entry."""

    validated = _validate_entry_shape(entry)

    try:
        return digest(
            AUDIT_ENTRY_OBJECT_TYPE,
            validated,
        )
    except CanonicalError as exc:
        raise AuditError("invalid audit entry") from exc


def validate_log(log: object) -> None:
    """Validate sequence, chronology, and hash linkage of an audit log."""

    if type(log) not in (tuple, list):
        raise AuditError("audit log must be a sequence")

    previous_digest = GENESIS_PREVIOUS_DIGEST
    previous_published_at: int | None = None

    for expected_sequence, entry in enumerate(log):
        validated = _validate_entry_shape(entry)

        if validated["sequence"] != expected_sequence:
            raise AuditError("invalid audit sequence")

        if validated["previous_digest"] != previous_digest:
            raise AuditError("broken audit hash link")

        published_at = validated["published_at"]

        if (
            previous_published_at is not None
            and published_at < previous_published_at
        ):
            raise AuditError("publication time regression")

        previous_digest = entry_digest(validated)
        previous_published_at = published_at


def validate_publications(
    log: object,
    bundles: object,
) -> None:
    """Verify that each audit entry matches its exact Step-4 bundle."""

    validate_log(log)

    if type(bundles) not in (tuple, list):
        raise AuditError("bundles must be a sequence")

    if len(log) != len(bundles):
        raise AuditError("publication cardinality mismatch")

    for entry, bundle in zip(log, bundles):
        try:
            expected_bundle_digest = bundle_digest(bundle)

            if type(bundle) is not dict:
                raise AuditError("invalid artifact bundle")

            review_result = bundle.get("review_result")

            if type(review_result) is not dict:
                raise AuditError("invalid artifact bundle")

            expected_run_id = review_result.get("run_id")
        except AuditError:
            raise
        except (
            ArtifactError,
            CanonicalError,
            KeyError,
            TypeError,
            ValueError,
        ) as exc:
            raise AuditError(
                "invalid artifact bundle"
            ) from exc

        expected_run_id = _require_hash(
            expected_run_id,
            "run_id",
        )

        expected_bundle_digest = _require_hash(
            expected_bundle_digest,
            "bundle_digest",
        )

        if entry["run_id"] != expected_run_id:
            raise AuditError(
                "audit run identity does not match bundle"
            )

        if (
            entry["bundle_digest"]
            != expected_bundle_digest
        ):
            raise AuditError(
                "audit bundle digest does not match bundle"
            )


def validate_extension(
    trusted_prefix: object,
    candidate: object,
) -> None:
    """Verify that candidate preserves a previously trusted audit prefix."""

    validate_log(trusted_prefix)
    validate_log(candidate)

    if len(candidate) < len(trusted_prefix):
        raise AuditError("audit log rollback")

    for index, trusted_entry in enumerate(
        trusted_prefix
    ):
        if candidate[index] != trusted_entry:
            raise AuditError(
                "trusted audit prefix was rewritten"
            )

def append_entry(
    log: object,
    *,
    bundle: object,
    published_at: int,
) -> tuple[dict[str, Any], ...]:
    """Append one bundle publication without mutating the supplied log."""

    validate_log(log)

    published_at = _require_nonnegative_int(
        published_at,
        "published_at",
    )

    if len(log) > 0:
        previous_published_at = log[-1]["published_at"]

        if published_at < previous_published_at:
            raise AuditError("publication time regression")

    try:
        current_bundle_digest = bundle_digest(bundle)
    except (ArtifactError, TypeError, ValueError) as exc:
        raise AuditError("invalid artifact bundle") from exc

    run_id = bundle["review_result"]["run_id"]

    _require_hash(run_id, "run_id")
    _require_hash(
        current_bundle_digest,
        "bundle_digest",
    )

    sequence = len(log)

    if sequence == 0:
        previous_digest = GENESIS_PREVIOUS_DIGEST
    else:
        previous_digest = entry_digest(log[-1])

    entry = {
        "schema": AUDIT_ENTRY_SCHEMA,
        "sequence": sequence,
        "previous_digest": previous_digest,
        "published_at": published_at,
        "run_id": run_id,
        "bundle_digest": current_bundle_digest,
    }

    _validate_entry_shape(entry)

    snapshot = tuple(
        deepcopy(existing)
        for existing in log
    )

    result = snapshot + (deepcopy(entry),)

    validate_log(result)

    return result
