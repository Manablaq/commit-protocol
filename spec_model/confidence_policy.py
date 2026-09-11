from __future__ import annotations


MAX_CONFIDENCE_BPS = 10_000

DECISION_READY = "DECISION_READY"
POLICY_ABSTAIN = "POLICY_ABSTAIN"

_ALLOWED_DECISIONS = (
    "COMMIT",
    "ABORT",
)


class PolicyError(ValueError):
    pass


def _require_bps(
    value: object,
    name: str,
) -> int:
    if (
        type(value) is not int
        or value < 0
        or value > MAX_CONFIDENCE_BPS
    ):
        raise PolicyError(
            name
            + " must be an integer from 0 to 10000"
        )

    return value


def confidence_gate(
    *,
    decision: object,
    confidence_bps: object,
    minimum_confidence_bps: object,
) -> str:
    if (
        type(decision) is not str
        or decision not in _ALLOWED_DECISIONS
    ):
        raise PolicyError(
            "decision must be COMMIT or ABORT"
        )

    confidence = _require_bps(
        confidence_bps,
        "confidence_bps",
    )

    minimum = _require_bps(
        minimum_confidence_bps,
        "minimum_confidence_bps",
    )

    if confidence < minimum:
        return POLICY_ABSTAIN

    return DECISION_READY
