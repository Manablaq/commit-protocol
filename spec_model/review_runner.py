"""Deterministic reference state machine for a COMMIT review run.

This model is deliberately off-chain. It does not replace COMMIT's mission
state machine or economic allocation logic. It provides a deterministic,
replay-safe orchestration model around one exact mission/evidence snapshot and
reuses the contract's ``commit-decision-v3`` consequential binding.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
import hashlib
import re

from .onchain import decision_nonce_v3, frame


_HEX_32 = re.compile(r"^[0-9a-f]{64}$")
_ALLOWED_DECISIONS = ("COMMIT", "ABORT")


class RunnerRejected(ValueError):
    """Raised when a review-run transition is not permitted."""


def _require_text(value: str, name: str, limit: int) -> str:
    if type(value) is not str or not value or len(value.encode("utf-8")) > limit:
        raise RunnerRejected(f"invalid {name}")
    return value


def _require_hash(value: str, name: str) -> str:
    if type(value) is not str or not _HEX_32.fullmatch(value):
        raise RunnerRejected(f"invalid {name}")
    return value


def derive_run_id(
    *,
    mission_id: str,
    mission_version: int,
    effect_root: str,
    sealed_evidence_root: str,
    active_evidence_root: str,
) -> str:
    """Derive the deterministic identity of one exact review snapshot."""

    _require_text(mission_id, "mission_id", 96)

    if type(mission_version) is not int or mission_version < 0:
        raise RunnerRejected("invalid mission_version")

    _require_hash(effect_root, "effect_root")
    _require_hash(sealed_evidence_root, "sealed_evidence_root")
    _require_hash(active_evidence_root, "active_evidence_root")

    fields = (
        mission_id,
        str(mission_version),
        effect_root,
        sealed_evidence_root,
        active_evidence_root,
    )

    payload = (
        "commit-review-run-v1"
        + "".join(frame(value) for value in fields)
    ).encode("utf-8")

    return hashlib.sha256(payload).hexdigest()


@dataclass(frozen=True)
class ReviewRun:
    mission_id: str
    mission_version: int
    effect_root: str
    sealed_evidence_root: str
    active_evidence_root: str
    phase: str = "created"
    terminal: bool = False
    decision: str = ""
    reason_code: str = ""
    decision_nonce: str = ""
    history: tuple[str, ...] = ()

    @property
    def run_id(self) -> str:
        return derive_run_id(
            mission_id=self.mission_id,
            mission_version=self.mission_version,
            effect_root=self.effect_root,
            sealed_evidence_root=self.sealed_evidence_root,
            active_evidence_root=self.active_evidence_root,
        )

    def check(self) -> None:
        derive_run_id(
            mission_id=self.mission_id,
            mission_version=self.mission_version,
            effect_root=self.effect_root,
            sealed_evidence_root=self.sealed_evidence_root,
            active_evidence_root=self.active_evidence_root,
        )

        assert self.phase in (
            "created",
            "running",
            "evidence_ready",
            "decided",
            "finalized",
        ), self

        assert type(self.terminal) is bool, self
        assert type(self.history) is tuple, self
        assert all(
            type(item) is str and item
            for item in self.history
        ), self

        expected_history = {
            "created": (),
            "running": (
                "created->running:start",
            ),
            "evidence_ready": (
                "created->running:start",
                "running->evidence_ready:evidence_ready",
            ),
            "decided": (
                "created->running:start",
                "running->evidence_ready:evidence_ready",
                "evidence_ready->decided:decision",
            ),
            "finalized": (
                "created->running:start",
                "running->evidence_ready:evidence_ready",
                "evidence_ready->decided:decision",
                "decided->finalized:finalize",
            ),
        }[self.phase]

        assert self.history == expected_history, self

        if self.phase in (
            "created",
            "running",
            "evidence_ready",
        ):
            assert not self.terminal, self
            assert self.decision == "", self
            assert self.reason_code == "", self
            assert self.decision_nonce == "", self

        elif self.phase == "decided":
            assert not self.terminal, self
            self._check_decision_binding()

        elif self.phase == "finalized":
            assert self.terminal, self
            self._check_decision_binding()

    def _check_decision_binding(self) -> None:
        assert self.decision in _ALLOWED_DECISIONS, self
        assert self.reason_code, self
        assert _HEX_32.fullmatch(self.decision_nonce), self

        expected_nonce = decision_nonce_v3(
            mission_id=self.mission_id,
            mission_version=self.mission_version,
            decision=self.decision,
            reason_code=self.reason_code,
            effect_root=self.effect_root,
            sealed_evidence_root=self.sealed_evidence_root,
            active_evidence_root=self.active_evidence_root,
        )

        assert self.decision_nonce == expected_nonce, self


def _record(
    run: ReviewRun,
    *,
    phase: str,
    event: str,
    terminal: bool | None = None,
    decision: str | None = None,
    reason_code: str | None = None,
    decision_nonce: str | None = None,
) -> ReviewRun:
    entry = f"{run.phase}->{phase}:{event}"

    return replace(
        run,
        phase=phase,
        terminal=run.terminal if terminal is None else terminal,
        decision=run.decision if decision is None else decision,
        reason_code=(
            run.reason_code
            if reason_code is None
            else reason_code
        ),
        decision_nonce=(
            run.decision_nonce
            if decision_nonce is None
            else decision_nonce
        ),
        history=run.history + (entry,),
    )


def step(
    run: ReviewRun,
    event: str,
    *,
    decision: str = "",
    reason_code: str = "",
    decision_nonce: str = "",
) -> ReviewRun:
    """Apply one deterministic review-run transition."""

    run.check()

    if event != "decision" and (
        decision
        or reason_code
        or decision_nonce
    ):
        raise RunnerRejected(
            "decision arguments are only valid for decision event"
        )

    if type(event) is not str or not event:
        raise RunnerRejected("invalid event")

    if run.phase == "finalized":
        if event == "finalize":
            return run
        raise RunnerRejected("run already terminal")

    if event == "start":
        if run.phase != "created":
            raise RunnerRejected("run cannot start")
        result = _record(
            run,
            phase="running",
            event=event,
        )

    elif event == "evidence_ready":
        if run.phase != "running":
            raise RunnerRejected("evidence not expected")
        result = _record(
            run,
            phase="evidence_ready",
            event=event,
        )

    elif event == "decision":
        if run.phase != "evidence_ready":
            raise RunnerRejected("decision not expected")

        if decision not in _ALLOWED_DECISIONS:
            raise RunnerRejected("invalid decision")

        _require_text(reason_code, "reason_code", 128)
        _require_hash(decision_nonce, "decision_nonce")

        expected = decision_nonce_v3(
            mission_id=run.mission_id,
            mission_version=run.mission_version,
            decision=decision,
            reason_code=reason_code,
            effect_root=run.effect_root,
            sealed_evidence_root=run.sealed_evidence_root,
            active_evidence_root=run.active_evidence_root,
        )

        if decision_nonce != expected:
            raise RunnerRejected("decision nonce mismatch")

        result = _record(
            run,
            phase="decided",
            event=event,
            decision=decision,
            reason_code=reason_code,
            decision_nonce=decision_nonce,
        )

    elif event == "finalize":
        if run.phase != "decided":
            raise RunnerRejected("run is not decided")
        result = _record(
            run,
            phase="finalized",
            event=event,
            terminal=True,
        )

    else:
        raise RunnerRejected("unknown event")

    result.check()
    return result


def canonical_result(run: ReviewRun) -> dict[str, object]:
    """Return the complete deterministic reviewer-facing run record."""

    run.check()

    return {
        "schema": "commit-review-run-v1",
        "run_id": run.run_id,
        "mission_id": run.mission_id,
        "mission_version": run.mission_version,
        "phase": run.phase,
        "terminal": run.terminal,
        "decision": run.decision,
        "reason_code": run.reason_code,
        "decision_nonce": run.decision_nonce,
        "effect_root": run.effect_root,
        "sealed_evidence_root": run.sealed_evidence_root,
        "active_evidence_root": run.active_evidence_root,
        "history": list(run.history),
    }
