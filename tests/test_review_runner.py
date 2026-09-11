import unittest
from dataclasses import replace

from spec_model.onchain import decision_nonce_v3
from spec_model.review_runner import (
    ReviewRun,
    RunnerRejected,
    canonical_result,
    derive_run_id,
    step,
)


MISSION_ID = "mission-runner-001"
MISSION_VERSION = 7
EFFECT_ROOT = "11" * 32
SEALED_ROOT = "22" * 32
ACTIVE_ROOT = "33" * 32


def nonce(decision="COMMIT", reason_code="semantic_acceptance"):
    return decision_nonce_v3(
        mission_id=MISSION_ID,
        mission_version=MISSION_VERSION,
        decision=decision,
        reason_code=reason_code,
        effect_root=EFFECT_ROOT,
        sealed_evidence_root=SEALED_ROOT,
        active_evidence_root=ACTIVE_ROOT,
    )


def fresh():
    return ReviewRun(
        mission_id=MISSION_ID,
        mission_version=MISSION_VERSION,
        effect_root=EFFECT_ROOT,
        sealed_evidence_root=SEALED_ROOT,
        active_evidence_root=ACTIVE_ROOT,
    )


class ReviewRunnerTests(unittest.TestCase):
    def test_run_id_is_deterministic_and_binds_review_identity(self):
        args = dict(
            mission_id=MISSION_ID,
            mission_version=MISSION_VERSION,
            effect_root=EFFECT_ROOT,
            sealed_evidence_root=SEALED_ROOT,
            active_evidence_root=ACTIVE_ROOT,
        )
        original = derive_run_id(**args)

        self.assertEqual(original, derive_run_id(**args))
        self.assertRegex(original, r"^[0-9a-f]{64}$")

        mutations = {
            "mission_id": "mission-runner-002",
            "mission_version": MISSION_VERSION + 1,
            "effect_root": "44" * 32,
            "sealed_evidence_root": "55" * 32,
            "active_evidence_root": "66" * 32,
        }
        for field, value in mutations.items():
            with self.subTest(field=field):
                self.assertNotEqual(
                    original,
                    derive_run_id(**{**args, field: value}),
                )

    def test_initial_state_is_created_with_empty_history(self):
        run = fresh()
        run.check()

        self.assertEqual(run.phase, "created")
        self.assertEqual(run.history, ())
        self.assertEqual(run.decision, "")
        self.assertEqual(run.reason_code, "")
        self.assertEqual(run.decision_nonce, "")
        self.assertFalse(run.terminal)

    def test_legal_commit_path_has_exact_transition_history(self):
        run = fresh()
        run = step(run, "start")
        run = step(run, "evidence_ready")
        run = step(
            run,
            "decision",
            decision="COMMIT",
            reason_code="semantic_acceptance",
            decision_nonce=nonce(),
        )
        run = step(run, "finalize")

        run.check()

        self.assertEqual(run.phase, "finalized")
        self.assertTrue(run.terminal)
        self.assertEqual(run.decision, "COMMIT")
        self.assertEqual(run.reason_code, "semantic_acceptance")
        self.assertEqual(run.decision_nonce, nonce())
        self.assertEqual(
            run.history,
            (
                "created->running:start",
                "running->evidence_ready:evidence_ready",
                "evidence_ready->decided:decision",
                "decided->finalized:finalize",
            ),
        )

    def test_legal_abort_path_reuses_exact_decision_v3_binding(self):
        run = fresh()
        run = step(run, "start")
        run = step(run, "evidence_ready")

        expected = nonce(
            decision="ABORT",
            reason_code="semantic_rejection",
        )
        run = step(
            run,
            "decision",
            decision="ABORT",
            reason_code="semantic_rejection",
            decision_nonce=expected,
        )

        self.assertEqual(run.decision_nonce, expected)

        with self.assertRaises(RunnerRejected):
            step(
                fresh(),
                "decision",
                decision="ABORT",
                reason_code="semantic_rejection",
                decision_nonce=expected,
            )

    def test_wrong_decision_nonce_is_rejected(self):
        run = step(step(fresh(), "start"), "evidence_ready")

        with self.assertRaises(RunnerRejected):
            step(
                run,
                "decision",
                decision="COMMIT",
                reason_code="semantic_acceptance",
                decision_nonce="ff" * 32,
            )

    def test_terminal_run_is_idempotent_for_exact_finalize_replay(self):
        run = fresh()
        run = step(run, "start")
        run = step(run, "evidence_ready")
        run = step(
            run,
            "decision",
            decision="COMMIT",
            reason_code="semantic_acceptance",
            decision_nonce=nonce(),
        )
        run = step(run, "finalize")

        self.assertEqual(step(run, "finalize"), run)

    def test_terminal_run_rejects_state_changing_replay(self):
        run = fresh()
        run = step(run, "start")
        run = step(run, "evidence_ready")
        run = step(
            run,
            "decision",
            decision="COMMIT",
            reason_code="semantic_acceptance",
            decision_nonce=nonce(),
        )
        run = step(run, "finalize")

        for event in ("start", "evidence_ready"):
            with self.subTest(event=event):
                with self.assertRaises(RunnerRejected):
                    step(run, event)

    def test_illegal_transition_is_rejected_without_mutation(self):
        run = fresh()

        with self.assertRaises(RunnerRejected):
            step(run, "evidence_ready")

        self.assertEqual(run, fresh())

    def test_invariant_rejects_terminal_state_without_decision_binding(self):
        faulty = replace(
            fresh(),
            phase="finalized",
            terminal=True,
        )

        with self.assertRaises(AssertionError):
            faulty.check()

    def test_canonical_result_is_deterministic_and_complete(self):
        run = fresh()
        run = step(run, "start")
        run = step(run, "evidence_ready")
        run = step(
            run,
            "decision",
            decision="COMMIT",
            reason_code="semantic_acceptance",
            decision_nonce=nonce(),
        )
        run = step(run, "finalize")

        first = canonical_result(run)
        second = canonical_result(run)

        self.assertEqual(first, second)
        self.assertEqual(
            set(first),
            {
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
            },
        )
        self.assertEqual(first["schema"], "commit-review-run-v1")
        self.assertEqual(first["run_id"], run.run_id)
        self.assertEqual(first["decision_nonce"], nonce())
        self.assertEqual(first["history"], list(run.history))


    def test_invariant_recomputes_decision_binding_after_decision_tamper(self):
        run = fresh()
        run = step(run, "start")
        run = step(run, "evidence_ready")
        run = step(
            run,
            "decision",
            decision="COMMIT",
            reason_code="semantic_acceptance",
            decision_nonce=nonce(),
        )
        run = step(run, "finalize")

        tampered = replace(
            run,
            decision="ABORT",
        )

        with self.assertRaises(AssertionError):
            tampered.check()

    def test_invariant_recomputes_decision_binding_after_reason_tamper(self):
        run = fresh()
        run = step(run, "start")
        run = step(run, "evidence_ready")
        run = step(
            run,
            "decision",
            decision="COMMIT",
            reason_code="semantic_acceptance",
            decision_nonce=nonce(),
        )
        run = step(run, "finalize")

        tampered = replace(
            run,
            reason_code="different_reason",
        )

        with self.assertRaises(AssertionError):
            tampered.check()

    def test_invariant_recomputes_decision_binding_after_root_tamper(self):
        run = fresh()
        run = step(run, "start")
        run = step(run, "evidence_ready")
        run = step(
            run,
            "decision",
            decision="COMMIT",
            reason_code="semantic_acceptance",
            decision_nonce=nonce(),
        )
        run = step(run, "finalize")

        for field, value in (
            ("effect_root", "44" * 32),
            ("sealed_evidence_root", "55" * 32),
            ("active_evidence_root", "66" * 32),
        ):
            with self.subTest(field=field):
                tampered = replace(
                    run,
                    **{field: value},
                )

                with self.assertRaises(AssertionError):
                    tampered.check()

    def test_invariant_rejects_finalized_history_tamper(self):
        run = fresh()
        run = step(run, "start")
        run = step(run, "evidence_ready")
        run = step(
            run,
            "decision",
            decision="COMMIT",
            reason_code="semantic_acceptance",
            decision_nonce=nonce(),
        )
        run = step(run, "finalize")

        mutations = (
            ("missing_history", ()),
            (
                "changed_transition",
                (
                    "created->running:start",
                    "running->evidence_ready:evidence_ready",
                    "evidence_ready->decided:WRONG",
                    "decided->finalized:finalize",
                ),
            ),
            (
                "extra_transition",
                run.history + ("finalized->finalized:fake",),
            ),
        )

        for name, history in mutations:
            with self.subTest(name=name):
                tampered = replace(
                    run,
                    history=history,
                )
                with self.assertRaises(AssertionError):
                    tampered.check()

    def test_non_decision_events_reject_decision_arguments(self):
        created = fresh()
        running = step(created, "start")
        ready = step(running, "evidence_ready")
        decided = step(
            ready,
            "decision",
            decision="COMMIT",
            reason_code="semantic_acceptance",
            decision_nonce=nonce(),
        )
        finalized = step(decided, "finalize")

        vectors = (
            (
                "start_with_decision_fields",
                created,
                "start",
            ),
            (
                "evidence_ready_with_decision_fields",
                running,
                "evidence_ready",
            ),
            (
                "finalize_with_decision_fields",
                decided,
                "finalize",
            ),
            (
                "finalized_replay_with_decision_fields",
                finalized,
                "finalize",
            ),
        )

        for name, run, event in vectors:
            with self.subTest(name=name):
                with self.assertRaises(RunnerRejected):
                    step(
                        run,
                        event,
                        decision="ABORT",
                        reason_code="extraneous",
                        decision_nonce="44" * 32,
                    )


if __name__ == "__main__":
    unittest.main()
