"""Deterministic reproducibility binding for confidence review inputs."""

from __future__ import annotations

import hashlib
import re

from spec_model.confidence_policy import MAX_CONFIDENCE_BPS


REVIEW_INPUT_SCHEMA = "commit-review-confidence-input-v1"
PROVENANCE_SCOPE = "REPRODUCIBILITY_ONLY"
AUTHENTICITY = "UNVERIFIED"

_ALLOWED_DECISIONS = {
    "COMMIT",
    "ABORT",
}

_FIELDS = {
    "schema",
    "decision",
    "confidence_bps",
    "review_input_sha256",
    "derivation_method",
    "derivation_version",
    "derivation_sha256",
    "provenance_scope",
    "authenticity",
}

_LABEL_RE = re.compile(
    r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}"
)

_HASH_RE = re.compile(
    r"[0-9a-f]{64}"
)


class ReviewInputError(ValueError):
    """Raised when a reproducibility binding is invalid."""


def _require_decision(
    value: object,
) -> str:
    if (
        type(value) is not str
        or value not in _ALLOWED_DECISIONS
    ):
        raise ReviewInputError(
            "decision must be COMMIT or ABORT"
        )

    return value


def _require_confidence_bps(
    value: object,
) -> int:
    if (
        type(value) is not int
        or value < 0
        or value > MAX_CONFIDENCE_BPS
    ):
        raise ReviewInputError(
            "confidence_bps must be an integer from 0 to 10000"
        )

    return value


def _require_material(
    value: object,
    name: str,
) -> bytes:
    if (
        type(value) is not bytes
        or not value
    ):
        raise ReviewInputError(
            name
            + " must be non-empty bytes"
        )

    return value


def _require_label(
    value: object,
    name: str,
) -> str:
    if (
        type(value) is not str
        or _LABEL_RE.fullmatch(
            value
        )
        is None
    ):
        raise ReviewInputError(
            name
            + " must be a non-empty ASCII label"
        )

    return value


def _require_hash(
    value: object,
    name: str,
) -> str:
    if (
        type(value) is not str
        or _HASH_RE.fullmatch(
            value
        )
        is None
    ):
        raise ReviewInputError(
            name
            + " must be lowercase SHA-256 hex"
        )

    return value


def validate_review_input_binding(
    binding: object,
) -> dict[str, object]:
    if type(binding) is not dict:
        raise ReviewInputError(
            "review input binding must be an object"
        )

    if set(binding) != _FIELDS:
        raise ReviewInputError(
            "invalid review input binding fields"
        )

    if (
        binding.get(
            "schema"
        )
        != REVIEW_INPUT_SCHEMA
    ):
        raise ReviewInputError(
            "invalid review input schema"
        )

    if (
        binding.get(
            "provenance_scope"
        )
        != PROVENANCE_SCOPE
    ):
        raise ReviewInputError(
            "invalid provenance scope"
        )

    if (
        binding.get(
            "authenticity"
        )
        != AUTHENTICITY
    ):
        raise ReviewInputError(
            "invalid authenticity value"
        )

    decision = _require_decision(
        binding.get(
            "decision"
        )
    )

    confidence_bps = (
        _require_confidence_bps(
            binding.get(
                "confidence_bps"
            )
        )
    )

    review_input_sha256 = (
        _require_hash(
            binding.get(
                "review_input_sha256"
            ),
            "review_input_sha256",
        )
    )

    derivation_method = (
        _require_label(
            binding.get(
                "derivation_method"
            ),
            "derivation_method",
        )
    )

    derivation_version = (
        _require_label(
            binding.get(
                "derivation_version"
            ),
            "derivation_version",
        )
    )

    derivation_sha256 = (
        _require_hash(
            binding.get(
                "derivation_sha256"
            ),
            "derivation_sha256",
        )
    )

    return {
        "schema": REVIEW_INPUT_SCHEMA,
        "decision": decision,
        "confidence_bps": confidence_bps,
        "review_input_sha256": (
            review_input_sha256
        ),
        "derivation_method": (
            derivation_method
        ),
        "derivation_version": (
            derivation_version
        ),
        "derivation_sha256": (
            derivation_sha256
        ),
        "provenance_scope": (
            PROVENANCE_SCOPE
        ),
        "authenticity": AUTHENTICITY,
    }


def review_input_binding(
    *,
    decision: object,
    confidence_bps: object,
    review_input_bytes: object,
    derivation_method: object,
    derivation_version: object,
    derivation_bytes: object,
) -> dict[str, object]:
    validated_decision = (
        _require_decision(
            decision
        )
    )

    validated_confidence = (
        _require_confidence_bps(
            confidence_bps
        )
    )

    validated_input = (
        _require_material(
            review_input_bytes,
            "review_input_bytes",
        )
    )

    validated_method = (
        _require_label(
            derivation_method,
            "derivation_method",
        )
    )

    validated_version = (
        _require_label(
            derivation_version,
            "derivation_version",
        )
    )

    validated_derivation = (
        _require_material(
            derivation_bytes,
            "derivation_bytes",
        )
    )

    binding = {
        "schema": REVIEW_INPUT_SCHEMA,
        "decision": (
            validated_decision
        ),
        "confidence_bps": (
            validated_confidence
        ),
        "review_input_sha256": (
            hashlib.sha256(
                validated_input
            ).hexdigest()
        ),
        "derivation_method": (
            validated_method
        ),
        "derivation_version": (
            validated_version
        ),
        "derivation_sha256": (
            hashlib.sha256(
                validated_derivation
            ).hexdigest()
        ),
        "provenance_scope": (
            PROVENANCE_SCOPE
        ),
        "authenticity": AUTHENTICITY,
    }

    return validate_review_input_binding(
        binding
    )


def verify_review_input_material(
    binding: object,
    *,
    review_input_bytes: object,
    derivation_bytes: object,
) -> dict[str, object]:
    validated = (
        validate_review_input_binding(
            binding
        )
    )

    validated_input = (
        _require_material(
            review_input_bytes,
            "review_input_bytes",
        )
    )

    validated_derivation = (
        _require_material(
            derivation_bytes,
            "derivation_bytes",
        )
    )

    input_digest = hashlib.sha256(
        validated_input
    ).hexdigest()

    derivation_digest = hashlib.sha256(
        validated_derivation
    ).hexdigest()

    if (
        input_digest
        != validated[
            "review_input_sha256"
        ]
    ):
        raise ReviewInputError(
            "review input bytes do not match binding"
        )

    if (
        derivation_digest
        != validated[
            "derivation_sha256"
        ]
    ):
        raise ReviewInputError(
            "derivation bytes do not match binding"
        )

    return validated
