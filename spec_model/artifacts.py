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
from spec_model.confidence_policy import (
    DECISION_READY,
    POLICY_ABSTAIN,
    PolicyError,
    confidence_gate,
)
from spec_model.review_input import (
    ReviewInputError,
    validate_review_input_binding,
)
from spec_model.review_runner import ReviewRun, canonical_result


BUNDLE_SCHEMA = "commit-review-artifact-bundle-v1"
BUNDLE_OBJECT_TYPE = "review_artifact_bundle"
REVIEW_RESULT_SCHEMA = "commit-review-run-v1"
POLICY_BUNDLE_SCHEMA = "commit-review-artifact-bundle-v2"
POLICY_ASSESSMENT_SCHEMA = "commit-review-policy-assessment-v1"
REPRODUCIBLE_POLICY_BUNDLE_SCHEMA = "commit-review-artifact-bundle-v3"



_BUNDLE_FIELDS = {
    "schema",
    "review_result",
    "contract_source_sha256",
    "runtime_archive_sha256",
}

_POLICY_BUNDLE_FIELDS = {
    "schema",
    "review_result",
    "policy_assessment",
    "contract_source_sha256",
    "runtime_archive_sha256",
}

_REPRODUCIBLE_POLICY_BUNDLE_FIELDS = {
    "schema",
    "review_result",
    "policy_assessment",
    "review_input_binding",
    "contract_source_sha256",
    "runtime_archive_sha256",
}


_POLICY_ASSESSMENT_FIELDS = {
    "schema",
    "decision",
    "confidence_bps",
    "minimum_confidence_bps",
    "outcome",
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


def _validate_policy_assessment(
    policy_assessment: object,
) -> dict[str, object]:
    if type(policy_assessment) is not dict:
        raise ArtifactError(
            "invalid policy_assessment"
        )

    if (
        set(policy_assessment)
        != _POLICY_ASSESSMENT_FIELDS
    ):
        raise ArtifactError(
            "invalid policy_assessment fields"
        )

    if (
        policy_assessment.get(
            "schema"
        )
        != POLICY_ASSESSMENT_SCHEMA
    ):
        raise ArtifactError(
            "invalid policy_assessment schema"
        )

    decision = (
        policy_assessment.get(
            "decision"
        )
    )

    confidence_bps = (
        policy_assessment.get(
            "confidence_bps"
        )
    )

    minimum_confidence_bps = (
        policy_assessment.get(
            "minimum_confidence_bps"
        )
    )

    outcome = (
        policy_assessment.get(
            "outcome"
        )
    )

    try:
        expected_outcome = (
            confidence_gate(
                decision=decision,
                confidence_bps=(
                    confidence_bps
                ),
                minimum_confidence_bps=(
                    minimum_confidence_bps
                ),
            )
        )
    except PolicyError as exc:
        raise ArtifactError(
            "invalid policy_assessment"
        ) from exc

    if outcome != expected_outcome:
        raise ArtifactError(
            "policy_assessment outcome mismatch"
        )

    return {
        "schema": (
            POLICY_ASSESSMENT_SCHEMA
        ),
        "decision": decision,
        "confidence_bps": (
            confidence_bps
        ),
        "minimum_confidence_bps": (
            minimum_confidence_bps
        ),
        "outcome": outcome,
    }


def _validate_policy_run_binding(
    review_result: dict[str, object],
    policy_assessment: dict[str, object],
) -> None:
    outcome = (
        policy_assessment[
            "outcome"
        ]
    )

    phase = (
        review_result[
            "phase"
        ]
    )

    if outcome == POLICY_ABSTAIN:
        if phase != "evidence_ready":
            raise ArtifactError(
                "POLICY_ABSTAIN requires evidence_ready review"
            )

        if (
            review_result[
                "decision"
            ]
            != ""
        ):
            raise ArtifactError(
                "POLICY_ABSTAIN cannot bind a review decision"
            )

        return

    if outcome == DECISION_READY:
        if phase not in (
            "decided",
            "finalized",
        ):
            raise ArtifactError(
                "DECISION_READY requires decided or finalized review"
            )

        if (
            review_result[
                "decision"
            ]
            != policy_assessment[
                "decision"
            ]
        ):
            raise ArtifactError(
                "policy decision does not match review decision"
            )

        return

    raise ArtifactError(
        "invalid policy_assessment outcome"
    )


def policy_artifact_bundle(
    *,
    review_result: object,
    policy_assessment: object,
    contract_source_sha256: str,
    runtime_archive_sha256: str,
) -> dict[str, Any]:
    """Build a deterministic policy-aware reviewer artifact bundle."""

    validated_result = (
        _validate_review_result(
            review_result
        )
    )

    validated_assessment = (
        _validate_policy_assessment(
            policy_assessment
        )
    )

    _validate_policy_run_binding(
        validated_result,
        validated_assessment,
    )

    return {
        "schema": (
            POLICY_BUNDLE_SCHEMA
        ),
        "review_result": (
            validated_result
        ),
        "policy_assessment": (
            validated_assessment
        ),
        "contract_source_sha256": (
            _require_hash(
                contract_source_sha256,
                "contract_source_sha256",
            )
        ),
        "runtime_archive_sha256": (
            _require_hash(
                runtime_archive_sha256,
                "runtime_archive_sha256",
            )
        ),
    }


def _validate_reproducible_review_input(
    review_input_binding: object,
) -> dict[str, object]:
    try:
        return validate_review_input_binding(
            review_input_binding
        )
    except ReviewInputError as exc:
        raise ArtifactError(
            "invalid review_input_binding"
        ) from exc


def _validate_review_input_policy_cross_binding(
    policy_assessment: dict[str, object],
    review_input_binding: dict[str, object],
) -> None:
    if (
        review_input_binding[
            "decision"
        ]
        != policy_assessment[
            "decision"
        ]
    ):
        raise ArtifactError(
            "review input decision does not match policy assessment"
        )

    if (
        review_input_binding[
            "confidence_bps"
        ]
        != policy_assessment[
            "confidence_bps"
        ]
    ):
        raise ArtifactError(
            "review input confidence does not match policy assessment"
        )


def review_input_policy_artifact_bundle(
    *,
    review_result: object,
    policy_assessment: object,
    review_input_binding: object,
    contract_source_sha256: str,
    runtime_archive_sha256: str,
) -> dict[str, Any]:
    """Build a reproducible policy-aware reviewer artifact bundle."""

    validated_result = (
        _validate_review_result(
            review_result
        )
    )

    validated_assessment = (
        _validate_policy_assessment(
            policy_assessment
        )
    )

    _validate_policy_run_binding(
        validated_result,
        validated_assessment,
    )

    validated_review_input = (
        _validate_reproducible_review_input(
            review_input_binding
        )
    )

    _validate_review_input_policy_cross_binding(
        validated_assessment,
        validated_review_input,
    )

    return {
        "schema": (
            REPRODUCIBLE_POLICY_BUNDLE_SCHEMA
        ),
        "review_result": (
            validated_result
        ),
        "policy_assessment": (
            validated_assessment
        ),
        "review_input_binding": (
            validated_review_input
        ),
        "contract_source_sha256": (
            _require_hash(
                contract_source_sha256,
                "contract_source_sha256",
            )
        ),
        "runtime_archive_sha256": (
            _require_hash(
                runtime_archive_sha256,
                "runtime_archive_sha256",
            )
        ),
    }


def _validate_reproducible_policy_bundle(
    bundle: dict[str, Any],
) -> dict[str, Any]:
    if (
        set(bundle)
        != _REPRODUCIBLE_POLICY_BUNDLE_FIELDS
    ):
        raise ArtifactError(
            "bundle fields do not match reproducible policy artifact schema"
        )

    validated_result = (
        _validate_review_result(
            bundle.get(
                "review_result"
            )
        )
    )

    validated_assessment = (
        _validate_policy_assessment(
            bundle.get(
                "policy_assessment"
            )
        )
    )

    _validate_policy_run_binding(
        validated_result,
        validated_assessment,
    )

    validated_review_input = (
        _validate_reproducible_review_input(
            bundle.get(
                "review_input_binding"
            )
        )
    )

    _validate_review_input_policy_cross_binding(
        validated_assessment,
        validated_review_input,
    )

    _require_hash(
        bundle.get(
            "contract_source_sha256"
        ),
        "contract_source_sha256",
    )

    _require_hash(
        bundle.get(
            "runtime_archive_sha256"
        ),
        "runtime_archive_sha256",
    )

    return bundle




def _validate_v1_bundle(
    bundle: dict[str, Any],
) -> dict[str, Any]:
    if (
        set(bundle)
        != _BUNDLE_FIELDS
    ):
        raise ArtifactError(
            "bundle fields do not match artifact schema"
        )

    _validate_review_result(
        bundle.get(
            "review_result"
        )
    )

    _require_hash(
        bundle.get(
            "contract_source_sha256"
        ),
        "contract_source_sha256",
    )

    _require_hash(
        bundle.get(
            "runtime_archive_sha256"
        ),
        "runtime_archive_sha256",
    )

    return bundle


def _validate_policy_bundle(
    bundle: dict[str, Any],
) -> dict[str, Any]:
    if (
        set(bundle)
        != _POLICY_BUNDLE_FIELDS
    ):
        raise ArtifactError(
            "bundle fields do not match policy artifact schema"
        )

    validated_result = (
        _validate_review_result(
            bundle.get(
                "review_result"
            )
        )
    )

    validated_assessment = (
        _validate_policy_assessment(
            bundle.get(
                "policy_assessment"
            )
        )
    )

    _validate_policy_run_binding(
        validated_result,
        validated_assessment,
    )

    _require_hash(
        bundle.get(
            "contract_source_sha256"
        ),
        "contract_source_sha256",
    )

    _require_hash(
        bundle.get(
            "runtime_archive_sha256"
        ),
        "runtime_archive_sha256",
    )

    return bundle


def _validate_bundle(
    bundle: object,
) -> dict[str, Any]:
    if type(bundle) is not dict:
        raise ArtifactError(
            "bundle must be an object"
        )

    schema = bundle.get(
        "schema"
    )

    if schema == BUNDLE_SCHEMA:
        return _validate_v1_bundle(
            bundle
        )

    if (
        schema
        == POLICY_BUNDLE_SCHEMA
    ):
        return _validate_policy_bundle(
            bundle
        )

    if (
        schema
        == REPRODUCIBLE_POLICY_BUNDLE_SCHEMA
    ):
        return _validate_reproducible_policy_bundle(
            bundle
        )

    raise ArtifactError(
        "invalid artifact bundle schema"
    )


def bundle_bytes(bundle: object) -> bytes:
    """Return protocol-canonical bytes for a validated artifact bundle."""

    validated = _validate_bundle(bundle)
    return encode(BUNDLE_OBJECT_TYPE, validated)


def bundle_digest(bundle: object) -> str:
    """Return the SHA-256 digest of the protocol-canonical artifact bundle."""

    validated = _validate_bundle(bundle)
    return digest(BUNDLE_OBJECT_TYPE, validated)
