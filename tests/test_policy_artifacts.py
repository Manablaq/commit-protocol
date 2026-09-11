from __future__ import annotations

import inspect
import unittest

from spec_model.audit_log import (
    append_entry,
    validate_log,
    validate_publications,
)
from spec_model.confidence_policy import (
    DECISION_READY,
    POLICY_ABSTAIN,
)
from spec_model.onchain import decision_nonce_v3
from spec_model.review_runner import (
    ReviewRun,
    canonical_result,
    step,
)


CONTRACT_SHA = "44" * 32
RUNTIME_SHA = "55" * 32


class PolicyArtifactTests(unittest.TestCase):
    @staticmethod
    def _artifacts():
        import spec_model.artifacts as artifacts

        return artifacts

    @staticmethod
    def _created(
        mission_id: str,
    ) -> ReviewRun:
        return ReviewRun(
            mission_id=mission_id,
            mission_version=1,
            effect_root="11" * 32,
            sealed_evidence_root="22" * 32,
            active_evidence_root="33" * 32,
        )

    @classmethod
    def _ready(
        cls,
        mission_id: str,
    ) -> ReviewRun:
        return step(
            step(
                cls._created(
                    mission_id
                ),
                "start",
            ),
            "evidence_ready",
        )

    @classmethod
    def _decided(
        cls,
        mission_id: str,
        decision: str,
    ) -> ReviewRun:
        ready = cls._ready(
            mission_id
        )

        reason_code = (
            "semantic_acceptance"
            if decision == "COMMIT"
            else "semantic_rejection"
        )

        nonce = decision_nonce_v3(
            mission_id=ready.mission_id,
            mission_version=ready.mission_version,
            decision=decision,
            reason_code=reason_code,
            effect_root=ready.effect_root,
            sealed_evidence_root=ready.sealed_evidence_root,
            active_evidence_root=ready.active_evidence_root,
        )

        return step(
            ready,
            "decision",
            decision=decision,
            reason_code=reason_code,
            decision_nonce=nonce,
        )

    @classmethod
    def _finalized(
        cls,
        mission_id: str,
        decision: str,
    ) -> ReviewRun:
        return step(
            cls._decided(
                mission_id,
                decision,
            ),
            "finalize",
        )

    @staticmethod
    def _assessment(
        *,
        decision: str = "COMMIT",
        confidence_bps: int = 8_000,
        minimum_confidence_bps: int = 8_000,
        outcome: str = DECISION_READY,
    ) -> dict[str, object]:
        return {
            "schema": "commit-review-policy-assessment-v1",
            "decision": decision,
            "confidence_bps": confidence_bps,
            "minimum_confidence_bps": minimum_confidence_bps,
            "outcome": outcome,
        }

    @classmethod
    def _policy_bundle(
        cls,
        run: ReviewRun,
        assessment: dict[str, object],
    ) -> dict[str, object]:
        artifacts = cls._artifacts()

        return artifacts.policy_artifact_bundle(
            review_result=canonical_result(
                run
            ),
            policy_assessment=assessment,
            contract_source_sha256=CONTRACT_SHA,
            runtime_archive_sha256=RUNTIME_SHA,
        )

    def test_v1_bundle_remains_supported(self):
        artifacts = self._artifacts()

        bundle = artifacts.artifact_bundle(
            review_result=canonical_result(
                self._created(
                    "policy-v1-compat"
                )
            ),
            contract_source_sha256=CONTRACT_SHA,
            runtime_archive_sha256=RUNTIME_SHA,
        )

        self.assertEqual(
            bundle["schema"],
            "commit-review-artifact-bundle-v1",
        )

        self.assertRegex(
            artifacts.bundle_digest(
                bundle
            ),
            r"^[0-9a-f]{64}$",
        )

    def test_policy_bundle_surface_is_versioned_without_replacing_v1(self):
        artifacts = self._artifacts()

        self.assertEqual(
            artifacts.BUNDLE_SCHEMA,
            "commit-review-artifact-bundle-v1",
        )

        self.assertEqual(
            artifacts.POLICY_BUNDLE_SCHEMA,
            "commit-review-artifact-bundle-v2",
        )

        self.assertEqual(
            artifacts.POLICY_ASSESSMENT_SCHEMA,
            "commit-review-policy-assessment-v1",
        )

        signature = inspect.signature(
            artifacts.policy_artifact_bundle
        )

        self.assertEqual(
            list(signature.parameters),
            [
                "review_result",
                "policy_assessment",
                "contract_source_sha256",
                "runtime_archive_sha256",
            ],
        )

        for parameter in signature.parameters.values():
            self.assertIs(
                parameter.kind,
                inspect.Parameter.KEYWORD_ONLY,
            )
            self.assertIs(
                parameter.default,
                inspect.Parameter.empty,
            )

    def test_policy_abstain_accepts_only_evidence_ready_run(self):
        artifacts = self._artifacts()

        ready = self._ready(
            "policy-abstain-ready"
        )

        bundle = self._policy_bundle(
            ready,
            self._assessment(
                confidence_bps=7_999,
                minimum_confidence_bps=8_000,
                outcome=POLICY_ABSTAIN,
            ),
        )

        self.assertEqual(
            bundle["schema"],
            artifacts.POLICY_BUNDLE_SCHEMA,
        )

        self.assertEqual(
            bundle["policy_assessment"]["outcome"],
            POLICY_ABSTAIN,
        )

        self.assertEqual(
            bundle["review_result"]["phase"],
            "evidence_ready",
        )

        self.assertEqual(
            bundle["review_result"]["decision"],
            "",
        )

    def test_policy_abstain_rejects_decided_and_finalized_runs(self):
        artifacts = self._artifacts()

        assessment = self._assessment(
            confidence_bps=7_999,
            minimum_confidence_bps=8_000,
            outcome=POLICY_ABSTAIN,
        )

        for run in (
            self._decided(
                "policy-abstain-decided",
                "COMMIT",
            ),
            self._finalized(
                "policy-abstain-finalized",
                "COMMIT",
            ),
        ):
            with self.subTest(
                phase=run.phase,
            ):
                with self.assertRaises(
                    artifacts.ArtifactError
                ):
                    self._policy_bundle(
                        run,
                        assessment,
                    )

    def test_decision_ready_accepts_matching_decided_and_finalized_runs(self):
        for phase in (
            "decided",
            "finalized",
        ):
            for decision in (
                "COMMIT",
                "ABORT",
            ):
                with self.subTest(
                    phase=phase,
                    decision=decision,
                ):
                    if phase == "decided":
                        run = self._decided(
                            "policy-ready-"
                            + phase
                            + "-"
                            + decision.lower(),
                            decision,
                        )
                    else:
                        run = self._finalized(
                            "policy-ready-"
                            + phase
                            + "-"
                            + decision.lower(),
                            decision,
                        )

                    bundle = self._policy_bundle(
                        run,
                        self._assessment(
                            decision=decision,
                            confidence_bps=8_000,
                            minimum_confidence_bps=8_000,
                            outcome=DECISION_READY,
                        ),
                    )

                    self.assertEqual(
                        bundle["policy_assessment"]["decision"],
                        run.decision,
                    )

                    self.assertEqual(
                        bundle["policy_assessment"]["outcome"],
                        DECISION_READY,
                    )

    def test_decision_ready_rejects_evidence_ready_run(self):
        artifacts = self._artifacts()

        with self.assertRaises(
            artifacts.ArtifactError
        ):
            self._policy_bundle(
                self._ready(
                    "policy-ready-too-early"
                ),
                self._assessment(
                    decision="COMMIT",
                    confidence_bps=8_000,
                    minimum_confidence_bps=8_000,
                    outcome=DECISION_READY,
                ),
            )

    def test_decision_ready_requires_matching_review_decision(self):
        artifacts = self._artifacts()

        run = self._decided(
            "policy-ready-mismatch",
            "COMMIT",
        )

        with self.assertRaises(
            artifacts.ArtifactError
        ):
            self._policy_bundle(
                run,
                self._assessment(
                    decision="ABORT",
                    confidence_bps=9_000,
                    minimum_confidence_bps=8_000,
                    outcome=DECISION_READY,
                ),
            )

    def test_policy_assessment_outcome_must_match_confidence_gate(self):
        artifacts = self._artifacts()

        vectors = (
            (
                self._ready(
                    "policy-outcome-low"
                ),
                self._assessment(
                    confidence_bps=7_999,
                    minimum_confidence_bps=8_000,
                    outcome=DECISION_READY,
                ),
            ),
            (
                self._decided(
                    "policy-outcome-high",
                    "COMMIT",
                ),
                self._assessment(
                    confidence_bps=8_000,
                    minimum_confidence_bps=8_000,
                    outcome=POLICY_ABSTAIN,
                ),
            ),
        )

        for run, assessment in vectors:
            with self.subTest(
                mission_id=run.mission_id,
            ):
                with self.assertRaises(
                    artifacts.ArtifactError
                ):
                    self._policy_bundle(
                        run,
                        assessment,
                    )

    def test_policy_assessment_shape_and_bps_domain_are_strict(self):
        artifacts = self._artifacts()

        ready = self._ready(
            "policy-shape-domain"
        )

        valid = self._assessment(
            confidence_bps=7_999,
            minimum_confidence_bps=8_000,
            outcome=POLICY_ABSTAIN,
        )

        missing = dict(valid)
        missing.pop(
            "confidence_bps"
        )

        extra = {
            **valid,
            "source": "untrusted",
        }

        invalid_vectors = (
            missing,
            extra,
            {
                **valid,
                "schema": "wrong",
            },
            {
                **valid,
                "decision": "ABSTAIN",
            },
            {
                **valid,
                "confidence_bps": True,
            },
            {
                **valid,
                "confidence_bps": -1,
            },
            {
                **valid,
                "confidence_bps": 10_001,
            },
            {
                **valid,
                "minimum_confidence_bps": True,
            },
            {
                **valid,
                "minimum_confidence_bps": -1,
            },
            {
                **valid,
                "minimum_confidence_bps": 10_001,
            },
        )

        for assessment in invalid_vectors:
            with self.subTest(
                assessment=assessment,
            ):
                with self.assertRaises(
                    artifacts.ArtifactError
                ):
                    self._policy_bundle(
                        ready,
                        assessment,
                    )

    def test_policy_bundle_digest_binds_entire_assessment(self):
        artifacts = self._artifacts()

        run = self._decided(
            "policy-digest-binding",
            "COMMIT",
        )

        first = self._policy_bundle(
            run,
            self._assessment(
                decision="COMMIT",
                confidence_bps=8_000,
                minimum_confidence_bps=8_000,
                outcome=DECISION_READY,
            ),
        )

        second = self._policy_bundle(
            run,
            self._assessment(
                decision="COMMIT",
                confidence_bps=9_000,
                minimum_confidence_bps=8_000,
                outcome=DECISION_READY,
            ),
        )

        self.assertEqual(
            first["review_result"]["run_id"],
            second["review_result"]["run_id"],
        )

        self.assertNotEqual(
            artifacts.bundle_digest(
                first
            ),
            artifacts.bundle_digest(
                second
            ),
        )

    def test_policy_bundle_does_not_rederive_run_identity(self):
        run = self._ready(
            "policy-run-id-stability"
        )

        expected = canonical_result(
            run
        )

        bundle = self._policy_bundle(
            run,
            self._assessment(
                decision="COMMIT",
                confidence_bps=7_999,
                minimum_confidence_bps=8_000,
                outcome=POLICY_ABSTAIN,
            ),
        )

        self.assertEqual(
            bundle["review_result"],
            expected,
        )

        self.assertEqual(
            bundle["review_result"]["run_id"],
            run.run_id,
        )

    def test_existing_audit_schema_authenticates_policy_bundle(self):
        bundle = self._policy_bundle(
            self._ready(
                "policy-audit-compat"
            ),
            self._assessment(
                decision="ABORT",
                confidence_bps=6_000,
                minimum_confidence_bps=7_000,
                outcome=POLICY_ABSTAIN,
            ),
        )

        log = append_entry(
            (),
            bundle=bundle,
            published_at=1234,
        )

        validate_log(
            log
        )

        validate_publications(
            log,
            (bundle,),
        )

        self.assertEqual(
            len(log),
            1,
        )

        self.assertEqual(
            log[0]["run_id"],
            bundle["review_result"]["run_id"],
        )


if __name__ == "__main__":
    unittest.main()
