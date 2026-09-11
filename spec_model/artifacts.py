"""Deterministic reviewer artifact bundles for COMMIT.

This module defines the Step-4 artifact schema on top of the protocol-wide
canonical encoding primitives. Publication chronology and append-only audit
history are deliberately outside this module.
"""

from __future__ import annotations

from typing import Any

from spec_model.canonical import (
    CanonicalError,
    digest,
    encode,
    require_hash,
)
from spec_model.review_runner import ReviewRun, canonical_result


BUNDLE_SCHEMA = "commit-review-artifact-bundle-v1"
BUNDLE_OBJECT_TYPE = "review_artifact_bundle"
REVIEW_RESULT_SCHEMA = "commit-review-run-v1"

_BUNDLE_FIELDS = {
    "schema",
    "review_result",
    "contract_source_sha256",
    "runtime_archive_sha256",
}

_REVIEW_RESULT_FIELDS = {
    "schema",
    "run_id",
    "mission_id",
    "mission_version",
    "phase",
    "terminal",
    "decision",
    "reason_code",
    "decision_nonce",
    "effect_root",
    "sealed_evidence_root",
    "active_evidence_root",
    "history",
}

_PHASES = {
    "created",
    "running",
    "evidence_ready",
    "decided",
    "finalized",
}


class ArtifactError(ValueError):
    """Raised when an artifact bundle violates the Step-4 schema."""


def _require_hash(value: object, name: str) -> str:
    if type(value) is not str:
        raise ArtifactError(f"{name} must be lowercase SHA-256 hex")

    try:
        return require_hash(value, name)
    except CanonicalError as exc:
        raise ArtifactError(str(exc)) from exc


def _validate_review_result(review_result: object) -> dict[str, object]:
    if type(review_result) is not dict:
        raise ArtifactError("invalid review_result")

    expected_keys = {
        "schema",
        "run_id",
        "mission_id",
        "mission_version",
        "phase",
        "terminal",
        "decision",
        "reason_code",
        "decision_nonce",
        "effect_root",
        "sealed_evidence_root",
        "active_evidence_root",
        "history",
    }

    if set(review_result) != expected_keys:
        raise ArtifactError("invalid review_result fields")

    if review_result["schema"] != "commit-review-run-v1":
        raise ArtifactError("invalid review_result schema")

    history = review_result["history"]

    if type(history) is not list:
        raise ArtifactError("invalid review_result history")

    if not all(type(item) is str and item for item in history):
        raise ArtifactError("invalid review_result history")

    try:
        reconstructed = ReviewRun(
            mission_id=review_result["mission_id"],
            mission_version=review_result["mission_version"],
            effect_root=review_result["effect_root"],
            sealed_evidence_root=review_result["sealed_evidence_root"],
            active_evidence_root=review_result["active_evidence_root"],
            phase=review_result["phase"],
            terminal=review_result["terminal"],
            decision=review_result["decision"],
            reason_code=review_result["reason_code"],
            decision_nonce=review_result["decision_nonce"],
            history=tuple(history),
        )

        reconstructed.check()
        canonical = canonical_result(reconstructed)
    except (AssertionError, TypeError, ValueError) as exc:
        raise ArtifactError("invalid review_result") from exc

    if canonical != review_result:
        raise ArtifactError("review_result is not canonical")

    return canonical


def artifact_bundle(
    *,
    review_result: object,
    contract_source_sha256: str,
    runtime_archive_sha256: str,
) -> dict[str, Any]:
    """Build the complete deterministic Step-4 reviewer artifact bundle."""

    validated_result = review_result = _validate_review_result(review_result)

    return {
        "schema": BUNDLE_SCHEMA,
        "review_result": validated_result,
        "contract_source_sha256": _require_hash(
            contract_source_sha256,
            "contract_source_sha256",
        ),
        "runtime_archive_sha256": _require_hash(
            runtime_archive_sha256,
            "runtime_archive_sha256",
        ),
    }


def _validate_bundle(bundle: object) -> dict[str, Any]:
    if type(bundle) is not dict:
        raise ArtifactError("bundle must be an object")

    if set(bundle) != _BUNDLE_FIELDS:
        raise ArtifactError("bundle fields do not match artifact schema")

    if bundle.get("schema") != BUNDLE_SCHEMA:
        raise ArtifactError("invalid artifact bundle schema")

    _validate_review_result(bundle.get("review_result"))
    _require_hash(
        bundle.get("contract_source_sha256"),
        "contract_source_sha256",
    )
    _require_hash(
        bundle.get("runtime_archive_sha256"),
        "runtime_archive_sha256",
    )

    return bundle


def bundle_bytes(bundle: object) -> bytes:
    """Return protocol-canonical bytes for a validated artifact bundle."""

    validated = _validate_bundle(bundle)
    return encode(BUNDLE_OBJECT_TYPE, validated)


def bundle_digest(bundle: object) -> str:
    """Return the SHA-256 digest of the protocol-canonical artifact bundle."""

    validated = _validate_bundle(bundle)
    return digest(BUNDLE_OBJECT_TYPE, validated)
