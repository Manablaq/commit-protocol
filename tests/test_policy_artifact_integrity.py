from __future__ import annotations

from copy import deepcopy
import unittest

from spec_model.artifacts import (
    ArtifactError,
    BUNDLE_SCHEMA,
    POLICY_ASSESSMENT_SCHEMA,
    POLICY_BUNDLE_SCHEMA,
    artifact_bundle,
    bundle_digest,
    policy_artifact_bundle,
)
from spec_model.audit_log import (
    AuditError,
    append_entry,
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


class PolicyArtifactIntegrityTests(unittest.TestCase):
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
        decision: str,
        confidence_bps: int,
        minimum_confidence_bps: int,
        outcome: str,
    ) -> dict[str, object]:
        return {
            "schema": (
                POLICY_ASSESSMENT_SCHEMA
            ),
            "decision": decision,
            "confidence_bps": confidence_bps,
            "minimum_confidence_bps": (
                minimum_confidence_bps
            ),
            "outcome": outcome,
        }

    @classmethod
    def _abstain_bundle(
        cls,
        mission_id: str,
        *,
        decision: str = "COMMIT",
        confidence_bps: int = 7_999,
        minimum_confidence_bps: int = 8_000,
    ) -> dict[str, object]:
        return policy_artifact_bundle(
            review_result=canonical_result(
                cls._ready(
                    mission_id
                )
            ),
            policy_assessment=cls._assessment(
                decision=decision,
                confidence_bps=confidence_bps,
                minimum_confidence_bps=(
                    minimum_confidence_bps
                ),
                outcome=POLICY_ABSTAIN,
            ),
            contract_source_sha256=(
                CONTRACT_SHA
            ),
            runtime_archive_sha256=(
                RUNTIME_SHA
            ),
        )

    @classmethod
    def _decision_bundle(
        cls,
        mission_id: str,
        *,
        decision: str = "COMMIT",
        finalized: bool = False,
        confidence_bps: int = 8_000,
        minimum_confidence_bps: int = 8_000,
    ) -> dict[str, object]:
        if finalized:
            run = cls._finalized(
                mission_id,
                decision,
            )
        else:
            run = cls._decided(
                mission_id,
                decision,
            )

        return policy_artifact_bundle(
            review_result=canonical_result(
                run
            ),
            policy_assessment=cls._assessment(
                decision=decision,
                confidence_bps=confidence_bps,
                minimum_confidence_bps=(
                    minimum_confidence_bps
                ),
                outcome=DECISION_READY,
            ),
            contract_source_sha256=(
                CONTRACT_SHA
            ),
            runtime_archive_sha256=(
                RUNTIME_SHA
            ),
        )

    def test_v1_rejects_policy_assessment_smuggling(self):
        bundle = artifact_bundle(
            review_result=canonical_result(
                self._ready(
                    "attack-v1-smuggling"
                )
            ),
            contract_source_sha256=CONTRACT_SHA,
            runtime_archive_sha256=RUNTIME_SHA,
        )

        self.assertEqual(
            bundle["schema"],
            BUNDLE_SCHEMA,
        )

        forged = deepcopy(
            bundle
        )

        forged[
            "policy_assessment"
        ] = self._assessment(
            decision="COMMIT",
            confidence_bps=7_999,
            minimum_confidence_bps=8_000,
            outcome=POLICY_ABSTAIN,
        )

        with self.assertRaises(
            ArtifactError
        ):
            bundle_digest(
                forged
            )

    def test_v2_rejects_missing_or_extra_top_level_fields(self):
        bundle = self._abstain_bundle(
            "attack-v2-shape"
        )

        missing = deepcopy(
            bundle
        )

        missing.pop(
            "policy_assessment"
        )

        extra = deepcopy(
            bundle
        )

        extra[
            "published_at"
        ] = 1234

        for forged in (
            missing,
            extra,
        ):
            with self.subTest(
                fields=sorted(
                    forged
                )
            ):
                with self.assertRaises(
                    ArtifactError
                ):
                    bundle_digest(
                        forged
                    )

    def test_schema_only_v1_v2_substitution_is_rejected(self):
        v1 = artifact_bundle(
            review_result=canonical_result(
                self._ready(
                    "attack-schema-v1"
                )
            ),
            contract_source_sha256=CONTRACT_SHA,
            runtime_archive_sha256=RUNTIME_SHA,
        )

        v2 = self._abstain_bundle(
            "attack-schema-v2"
        )

        forged_v1_as_v2 = deepcopy(
            v1
        )

        forged_v1_as_v2[
            "schema"
        ] = POLICY_BUNDLE_SCHEMA

        forged_v2_as_v1 = deepcopy(
            v2
        )

        forged_v2_as_v1[
            "schema"
        ] = BUNDLE_SCHEMA

        for forged in (
            forged_v1_as_v2,
            forged_v2_as_v1,
        ):
            with self.subTest(
                schema=forged[
                    "schema"
                ]
            ):
                with self.assertRaises(
                    ArtifactError
                ):
                    bundle_digest(
                        forged
                    )

    def test_policy_assessment_rejects_missing_or_extra_fields(self):
        bundle = self._abstain_bundle(
            "attack-assessment-shape"
        )

        missing = deepcopy(
            bundle
        )

        missing[
            "policy_assessment"
        ].pop(
            "confidence_bps"
        )

        extra = deepcopy(
            bundle
        )

        extra[
            "policy_assessment"
        ][
            "authority"
        ] = "unbound"

        for forged in (
            missing,
            extra,
        ):
            with self.subTest(
                assessment=forged[
                    "policy_assessment"
                ]
            ):
                with self.assertRaises(
                    ArtifactError
                ):
                    bundle_digest(
                        forged
                    )

    def test_policy_outcome_forgery_is_rejected(self):
        bundle = self._abstain_bundle(
            "attack-outcome-forgery"
        )

        forged = deepcopy(
            bundle
        )

        forged[
            "policy_assessment"
        ][
            "outcome"
        ] = DECISION_READY

        with self.assertRaises(
            ArtifactError
        ):
            bundle_digest(
                forged
            )

    def test_confidence_boundary_mutation_without_outcome_update_is_rejected(self):
        bundle = self._abstain_bundle(
            "attack-confidence-boundary",
            confidence_bps=7_999,
            minimum_confidence_bps=8_000,
        )

        forged = deepcopy(
            bundle
        )

        forged[
            "policy_assessment"
        ][
            "confidence_bps"
        ] = 8_000

        with self.assertRaises(
            ArtifactError
        ):
            bundle_digest(
                forged
            )

    def test_minimum_boundary_mutation_without_outcome_update_is_rejected(self):
        bundle = self._abstain_bundle(
            "attack-threshold-boundary",
            confidence_bps=7_999,
            minimum_confidence_bps=8_000,
        )

        forged = deepcopy(
            bundle
        )

        forged[
            "policy_assessment"
        ][
            "minimum_confidence_bps"
        ] = 7_999

        with self.assertRaises(
            ArtifactError
        ):
            bundle_digest(
                forged
            )

    def test_decision_substitution_is_rejected(self):
        bundle = self._decision_bundle(
            "attack-decision-substitution",
            decision="COMMIT",
        )

        forged = deepcopy(
            bundle
        )

        forged[
            "policy_assessment"
        ][
            "decision"
        ] = "ABORT"

        with self.assertRaises(
            ArtifactError
        ):
            bundle_digest(
                forged
            )

    def test_valid_policy_metadata_substitution_changes_digest(self):
        first = self._abstain_bundle(
            "attack-valid-substitution",
            confidence_bps=7_999,
            minimum_confidence_bps=8_000,
        )

        second = self._abstain_bundle(
            "attack-valid-substitution",
            confidence_bps=7_000,
            minimum_confidence_bps=8_000,
        )

        third = self._abstain_bundle(
            "attack-valid-substitution",
            confidence_bps=7_000,
            minimum_confidence_bps=9_000,
        )

        self.assertEqual(
            first[
                "review_result"
            ][
                "run_id"
            ],
            second[
                "review_result"
            ][
                "run_id"
            ],
        )

        self.assertEqual(
            second[
                "review_result"
            ][
                "run_id"
            ],
            third[
                "review_result"
            ][
                "run_id"
            ],
        )

        digests = {
            bundle_digest(
                first
            ),
            bundle_digest(
                second
            ),
            bundle_digest(
                third
            ),
        }

        self.assertEqual(
            len(
                digests
            ),
            3,
        )

    def test_post_publication_policy_mutation_breaks_audit_pairing(self):
        bundle = self._abstain_bundle(
            "attack-post-publication",
            confidence_bps=7_999,
            minimum_confidence_bps=8_000,
        )

        log = append_entry(
            (),
            bundle=bundle,
            published_at=1000,
        )

        mutated = deepcopy(
            bundle
        )

        mutated[
            "policy_assessment"
        ][
            "confidence_bps"
        ] = 7_000

        with self.assertRaises(
            AuditError
        ):
            validate_publications(
                log,
                (mutated,),
            )

    def test_audit_rejects_reordered_multiphase_policy_bundles(self):
        mission_id = (
            "attack-audit-reorder"
        )

        abstain = self._abstain_bundle(
            mission_id,
            decision="COMMIT",
            confidence_bps=7_999,
            minimum_confidence_bps=8_000,
        )

        decision_ready = (
            self._decision_bundle(
                mission_id,
                decision="COMMIT",
                confidence_bps=8_000,
                minimum_confidence_bps=8_000,
            )
        )

        self.assertEqual(
            abstain[
                "review_result"
            ][
                "run_id"
            ],
            decision_ready[
                "review_result"
            ][
                "run_id"
            ],
        )

        log = append_entry(
            (),
            bundle=abstain,
            published_at=1000,
        )

        log = append_entry(
            log,
            bundle=decision_ready,
            published_at=1001,
        )

        validate_publications(
            log,
            (
                abstain,
                decision_ready,
            ),
        )

        with self.assertRaises(
            AuditError
        ):
            validate_publications(
                log,
                (
                    decision_ready,
                    abstain,
                ),
            )

    def test_audit_rejects_cross_run_bundle_substitution(self):
        original = self._abstain_bundle(
            "attack-cross-run-original"
        )

        substitute = self._abstain_bundle(
            "attack-cross-run-substitute"
        )

        self.assertNotEqual(
            original[
                "review_result"
            ][
                "run_id"
            ],
            substitute[
                "review_result"
            ][
                "run_id"
            ],
        )

        log = append_entry(
            (),
            bundle=original,
            published_at=1000,
        )

        with self.assertRaises(
            AuditError
        ):
            validate_publications(
                log,
                (substitute,),
            )


if __name__ == "__main__":
    unittest.main()
