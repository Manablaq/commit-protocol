from copy import deepcopy
import unittest

from spec_model.artifacts import ArtifactError, artifact_bundle
from spec_model.onchain import decision_nonce_v3
from spec_model.review_runner import ReviewRun, canonical_result, step


class ArtifactIntegrityTests(unittest.TestCase):
    def _created_result(self) -> dict[str, object]:
        run = ReviewRun(
            mission_id="artifact-integrity-created",
            mission_version=3,
            effect_root="11" * 32,
            sealed_evidence_root="22" * 32,
            active_evidence_root="33" * 32,
        )
        return canonical_result(run)

    def _finalized_result(self) -> dict[str, object]:
        run = ReviewRun(
            mission_id="artifact-integrity-finalized",
            mission_version=7,
            effect_root="44" * 32,
            sealed_evidence_root="55" * 32,
            active_evidence_root="66" * 32,
        )

        run = step(run, "start")
        run = step(run, "evidence_ready")

        nonce = decision_nonce_v3(
            mission_id=run.mission_id,
            mission_version=run.mission_version,
            decision="COMMIT",
            reason_code="artifact_integrity",
            effect_root=run.effect_root,
            sealed_evidence_root=run.sealed_evidence_root,
            active_evidence_root=run.active_evidence_root,
        )

        run = step(
            run,
            "decision",
            decision="COMMIT",
            reason_code="artifact_integrity",
            decision_nonce=nonce,
        )

        return canonical_result(step(run, "finalize"))

    def _bundle(self, review_result: object) -> dict[str, object]:
        return artifact_bundle(
            review_result=review_result,
            contract_source_sha256="aa" * 32,
            runtime_archive_sha256="bb" * 32,
        )

    def test_created_result_invariants_are_revalidated(self):
        base = self._created_result()

        vectors = {}

        candidate = deepcopy(base)
        candidate["run_id"] = "99" * 32
        vectors["forged_run_id"] = candidate

        candidate = deepcopy(base)
        candidate["phase"] = "running"
        vectors["phase_without_history"] = candidate

        candidate = deepcopy(base)
        candidate["terminal"] = True
        vectors["created_marked_terminal"] = candidate

        candidate = deepcopy(base)
        candidate["history"] = ["created->running:start"]
        vectors["created_with_history"] = candidate

        for name, candidate in vectors.items():
            with self.subTest(name=name):
                with self.assertRaises(ArtifactError):
                    self._bundle(candidate)

    def test_finalized_result_decision_binding_is_revalidated(self):
        base = self._finalized_result()

        vectors = {}

        candidate = deepcopy(base)
        candidate["decision_nonce"] = "77" * 32
        vectors["forged_decision_nonce"] = candidate

        candidate = deepcopy(base)
        candidate["decision"] = "ABORT"
        vectors["decision_changed_without_nonce"] = candidate

        candidate = deepcopy(base)
        candidate["reason_code"] = "tampered"
        vectors["reason_changed_without_nonce"] = candidate

        candidate = deepcopy(base)
        candidate["effect_root"] = "88" * 32
        vectors["effect_root_changed_without_nonce"] = candidate

        candidate = deepcopy(base)
        candidate["sealed_evidence_root"] = "99" * 32
        vectors["sealed_root_changed_without_nonce"] = candidate

        candidate = deepcopy(base)
        candidate["active_evidence_root"] = "aa" * 32
        vectors["active_root_changed_without_nonce"] = candidate

        for name, candidate in vectors.items():
            with self.subTest(name=name):
                with self.assertRaises(ArtifactError):
                    self._bundle(candidate)

    def test_finalized_result_phase_history_and_terminality_are_revalidated(self):
        base = self._finalized_result()

        vectors = {}

        candidate = deepcopy(base)
        candidate["terminal"] = False
        vectors["finalized_marked_nonterminal"] = candidate

        candidate = deepcopy(base)
        candidate["history"] = []
        vectors["finalized_history_removed"] = candidate

        for name, candidate in vectors.items():
            with self.subTest(name=name):
                with self.assertRaises(ArtifactError):
                    self._bundle(candidate)

    def test_bundle_snapshots_review_result_input(self):
        source = self._created_result()

        expected = deepcopy(source)

        bundle = self._bundle(source)

        self.assertEqual(bundle["review_result"], expected)
        self.assertIsNot(bundle["review_result"], source)

        source["mission_id"] = "caller-mutated-mission"
        source["history"].append("caller-mutated-history")

        self.assertEqual(bundle["review_result"], expected)
        self.assertNotEqual(
            bundle["review_result"]["mission_id"],
            source["mission_id"],
        )
        self.assertNotEqual(
            bundle["review_result"]["history"],
            source["history"],
        )


if __name__ == "__main__":
    unittest.main()
