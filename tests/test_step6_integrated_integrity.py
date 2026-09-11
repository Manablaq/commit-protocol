from __future__ import annotations

from copy import deepcopy
import unittest

from spec_model.artifacts import (
    ArtifactError,
    bundle_digest,
    review_input_policy_artifact_bundle,
)
from spec_model.audit_log import (
    AuditError,
    append_entry,
    validate_extension,
    validate_publications,
)
from spec_model.confidence_policy import (
    DECISION_READY,
    POLICY_ABSTAIN,
    confidence_gate,
)
from spec_model.onchain import decision_nonce_v3
from spec_model.review_input import (
    ReviewInputError,
    review_input_binding,
    validate_review_input_binding,
    verify_review_input_material,
)
from spec_model.review_runner import (
    ReviewRun,
    canonical_result,
    step,
)


CONTRACT_SHA = "44" * 32
RUNTIME_SHA = "55" * 32


class Step6IntegratedIntegrityTests(
    unittest.TestCase
):
    @staticmethod
    def _review_bytes(
        suffix: bytes = b"",
    ) -> bytes:
        return (
            b'{"mission":"step6-integrated",'
            b'"evidence":"exact"}'
            + suffix
        )

    @staticmethod
    def _derivation_bytes(
        suffix: bytes = b"",
    ) -> bytes:
        return (
            b"method: semantic-confidence\n"
            b"version: 1.0.0\n"
            + suffix
        )

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
            sealed_evidence_root=(
                ready.sealed_evidence_root
            ),
            active_evidence_root=(
                ready.active_evidence_root
            ),
        )

        return step(
            ready,
            "decision",
            decision=decision,
            reason_code=reason_code,
            decision_nonce=nonce,
        )

    @classmethod
    def _binding(
        cls,
        *,
        decision: str,
        confidence_bps: int,
        review_suffix: bytes = b"",
        derivation_suffix: bytes = b"",
        derivation_version: str = "1.0.0",
    ) -> dict[str, object]:
        binding = review_input_binding(
            decision=decision,
            confidence_bps=confidence_bps,
            review_input_bytes=(
                cls._review_bytes(
                    review_suffix
                )
            ),
            derivation_method=(
                "semantic-confidence"
            ),
            derivation_version=(
                derivation_version
            ),
            derivation_bytes=(
                cls._derivation_bytes(
                    derivation_suffix
                )
            ),
        )

        return binding

    @classmethod
    def _verified_binding(
        cls,
        *,
        decision: str,
        confidence_bps: int,
        review_suffix: bytes = b"",
        derivation_suffix: bytes = b"",
    ) -> dict[str, object]:
        binding = cls._binding(
            decision=decision,
            confidence_bps=confidence_bps,
            review_suffix=review_suffix,
            derivation_suffix=(
                derivation_suffix
            ),
        )

        return verify_review_input_material(
            binding,
            review_input_bytes=(
                cls._review_bytes(
                    review_suffix
                )
            ),
            derivation_bytes=(
                cls._derivation_bytes(
                    derivation_suffix
                )
            ),
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
                "commit-review-policy-assessment-v1"
            ),
            "decision": decision,
            "confidence_bps": confidence_bps,
            "minimum_confidence_bps": (
                minimum_confidence_bps
            ),
            "outcome": outcome,
        }

    @classmethod
    def _bundle(
        cls,
        run: ReviewRun,
        *,
        decision: str,
        confidence_bps: int,
        minimum_confidence_bps: int,
        outcome: str,
        binding: dict[str, object] | None = None,
    ) -> dict[str, object]:
        if binding is None:
            binding = cls._verified_binding(
                decision=decision,
                confidence_bps=(
                    confidence_bps
                ),
            )

        return (
            review_input_policy_artifact_bundle(
                review_result=canonical_result(
                    run
                ),
                policy_assessment=(
                    cls._assessment(
                        decision=decision,
                        confidence_bps=(
                            confidence_bps
                        ),
                        minimum_confidence_bps=(
                            minimum_confidence_bps
                        ),
                        outcome=outcome,
                    )
                ),
                review_input_binding=binding,
                contract_source_sha256=(
                    CONTRACT_SHA
                ),
                runtime_archive_sha256=(
                    RUNTIME_SHA
                ),
            )
        )

    def test_low_confidence_policy_abstain_keeps_review_run_predecision(
        self,
    ):
        run = self._ready(
            "integrated-abstain"
        )

        outcome = confidence_gate(
            decision="COMMIT",
            confidence_bps=7_999,
            minimum_confidence_bps=8_000,
        )

        self.assertEqual(
            outcome,
            POLICY_ABSTAIN,
        )

        bundle = self._bundle(
            run,
            decision="COMMIT",
            confidence_bps=7_999,
            minimum_confidence_bps=8_000,
            outcome=outcome,
        )

        self.assertEqual(
            bundle[
                "review_result"
            ][
                "phase"
            ],
            "evidence_ready",
        )

        self.assertEqual(
            bundle[
                "review_result"
            ][
                "decision"
            ],
            "",
        )

        self.assertNotEqual(
            bundle[
                "policy_assessment"
            ][
                "outcome"
            ],
            bundle[
                "review_result"
            ][
                "decision"
            ],
        )

    def test_decision_ready_cross_binds_exact_decision_and_score_end_to_end(
        self,
    ):
        run = self._decided(
            "integrated-ready",
            "ABORT",
        )

        outcome = confidence_gate(
            decision="ABORT",
            confidence_bps=8_000,
            minimum_confidence_bps=8_000,
        )

        self.assertEqual(
            outcome,
            DECISION_READY,
        )

        bundle = self._bundle(
            run,
            decision="ABORT",
            confidence_bps=8_000,
            minimum_confidence_bps=8_000,
            outcome=outcome,
        )

        self.assertEqual(
            bundle[
                "review_result"
            ][
                "decision"
            ],
            "ABORT",
        )

        self.assertEqual(
            bundle[
                "policy_assessment"
            ][
                "decision"
            ],
            bundle[
                "review_input_binding"
            ][
                "decision"
            ],
        )

        self.assertEqual(
            bundle[
                "policy_assessment"
            ][
                "confidence_bps"
            ],
            bundle[
                "review_input_binding"
            ][
                "confidence_bps"
            ],
        )

    def test_forged_policy_outcome_is_rejected_with_verified_material(
        self,
    ):
        binding = self._verified_binding(
            decision="COMMIT",
            confidence_bps=7_999,
        )

        with self.assertRaises(
            ArtifactError
        ):
            self._bundle(
                self._ready(
                    "integrated-outcome-forgery"
                ),
                decision="COMMIT",
                confidence_bps=7_999,
                minimum_confidence_bps=8_000,
                outcome=DECISION_READY,
                binding=binding,
            )

    def test_structural_hash_substitution_does_not_equal_material_verification(
        self,
    ):
        binding = self._binding(
            decision="COMMIT",
            confidence_bps=7_999,
        )

        forged = {
            **binding,
            "review_input_sha256": (
                "00" * 32
            ),
        }

        validated = (
            validate_review_input_binding(
                forged
            )
        )

        self.assertEqual(
            validated[
                "review_input_sha256"
            ],
            "00" * 32,
        )

        bundle = self._bundle(
            self._ready(
                "integrated-structural-boundary"
            ),
            decision="COMMIT",
            confidence_bps=7_999,
            minimum_confidence_bps=8_000,
            outcome=POLICY_ABSTAIN,
            binding=forged,
        )

        self.assertEqual(
            bundle[
                "review_input_binding"
            ][
                "review_input_sha256"
            ],
            "00" * 32,
        )

        with self.assertRaises(
            ReviewInputError
        ):
            verify_review_input_material(
                forged,
                review_input_bytes=(
                    self._review_bytes()
                ),
                derivation_bytes=(
                    self._derivation_bytes()
                ),
            )

    def test_review_input_byte_substitution_fails_material_verification(
        self,
    ):
        binding = self._binding(
            decision="COMMIT",
            confidence_bps=7_999,
        )

        with self.assertRaises(
            ReviewInputError
        ):
            verify_review_input_material(
                binding,
                review_input_bytes=(
                    self._review_bytes(
                        b"-substituted"
                    )
                ),
                derivation_bytes=(
                    self._derivation_bytes()
                ),
            )

    def test_derivation_byte_substitution_fails_material_verification(
        self,
    ):
        binding = self._binding(
            decision="ABORT",
            confidence_bps=6_000,
        )

        with self.assertRaises(
            ReviewInputError
        ):
            verify_review_input_material(
                binding,
                review_input_bytes=(
                    self._review_bytes()
                ),
                derivation_bytes=(
                    self._derivation_bytes(
                        b"-substituted"
                    )
                ),
            )

    def test_post_publication_review_input_hash_mutation_breaks_audit_pairing(
        self,
    ):
        bundle = self._bundle(
            self._ready(
                "integrated-post-publish-input"
            ),
            decision="COMMIT",
            confidence_bps=7_999,
            minimum_confidence_bps=8_000,
            outcome=POLICY_ABSTAIN,
        )

        log = append_entry(
            (),
            bundle=bundle,
            published_at=100,
        )

        mutated = deepcopy(
            bundle
        )

        mutated[
            "review_input_binding"
        ][
            "review_input_sha256"
        ] = "00" * 32

        with self.assertRaises(
            AuditError
        ):
            validate_publications(
                log,
                (mutated,),
            )

    def test_post_publication_derivation_metadata_mutation_breaks_audit_pairing(
        self,
    ):
        bundle = self._bundle(
            self._ready(
                "integrated-post-publish-method"
            ),
            decision="ABORT",
            confidence_bps=6_000,
            minimum_confidence_bps=7_000,
            outcome=POLICY_ABSTAIN,
        )

        log = append_entry(
            (),
            bundle=bundle,
            published_at=200,
        )

        mutated = deepcopy(
            bundle
        )

        mutated[
            "review_input_binding"
        ][
            "derivation_version"
        ] = "1.0.1"

        with self.assertRaises(
            AuditError
        ):
            validate_publications(
                log,
                (mutated,),
            )

    def test_multiphase_v3_publication_order_is_authenticated(
        self,
    ):
        mission_id = (
            "integrated-multiphase"
        )

        ready = self._ready(
            mission_id
        )

        decided = self._decided(
            mission_id,
            "COMMIT",
        )

        abstain_bundle = self._bundle(
            ready,
            decision="COMMIT",
            confidence_bps=7_999,
            minimum_confidence_bps=8_000,
            outcome=POLICY_ABSTAIN,
        )

        ready_bundle = self._bundle(
            decided,
            decision="COMMIT",
            confidence_bps=8_500,
            minimum_confidence_bps=8_000,
            outcome=DECISION_READY,
        )

        self.assertEqual(
            abstain_bundle[
                "review_result"
            ][
                "run_id"
            ],
            ready_bundle[
                "review_result"
            ][
                "run_id"
            ],
        )

        log = append_entry(
            (),
            bundle=abstain_bundle,
            published_at=300,
        )

        log = append_entry(
            log,
            bundle=ready_bundle,
            published_at=301,
        )

        validate_publications(
            log,
            (
                abstain_bundle,
                ready_bundle,
            ),
        )

        with self.assertRaises(
            AuditError
        ):
            validate_publications(
                log,
                (
                    ready_bundle,
                    abstain_bundle,
                ),
            )

    def test_cross_run_v3_bundle_substitution_is_rejected(
        self,
    ):
        first = self._bundle(
            self._ready(
                "integrated-run-a"
            ),
            decision="COMMIT",
            confidence_bps=7_999,
            minimum_confidence_bps=8_000,
            outcome=POLICY_ABSTAIN,
        )

        second = self._bundle(
            self._ready(
                "integrated-run-b"
            ),
            decision="COMMIT",
            confidence_bps=7_999,
            minimum_confidence_bps=8_000,
            outcome=POLICY_ABSTAIN,
        )

        log = append_entry(
            (),
            bundle=first,
            published_at=400,
        )

        with self.assertRaises(
            AuditError
        ):
            validate_publications(
                log,
                (second,),
            )

    def test_valid_reproducibility_material_changes_digest_not_run_id(
        self,
    ):
        run = self._ready(
            "integrated-material-digest"
        )

        first_binding = (
            self._verified_binding(
                decision="COMMIT",
                confidence_bps=7_999,
                review_suffix=b"-one",
            )
        )

        second_binding = (
            self._verified_binding(
                decision="COMMIT",
                confidence_bps=7_999,
                review_suffix=b"-two",
            )
        )

        first = self._bundle(
            run,
            decision="COMMIT",
            confidence_bps=7_999,
            minimum_confidence_bps=8_000,
            outcome=POLICY_ABSTAIN,
            binding=first_binding,
        )

        second = self._bundle(
            run,
            decision="COMMIT",
            confidence_bps=7_999,
            minimum_confidence_bps=8_000,
            outcome=POLICY_ABSTAIN,
            binding=second_binding,
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

        self.assertNotEqual(
            first_binding[
                "review_input_sha256"
            ],
            second_binding[
                "review_input_sha256"
            ],
        )

        self.assertNotEqual(
            bundle_digest(
                first
            ),
            bundle_digest(
                second
            ),
        )

    def test_audit_extension_preserves_trusted_v3_prefix(
        self,
    ):
        first = self._bundle(
            self._ready(
                "integrated-prefix-a"
            ),
            decision="ABORT",
            confidence_bps=5_000,
            minimum_confidence_bps=6_000,
            outcome=POLICY_ABSTAIN,
        )

        second = self._bundle(
            self._ready(
                "integrated-prefix-b"
            ),
            decision="COMMIT",
            confidence_bps=7_000,
            minimum_confidence_bps=8_000,
            outcome=POLICY_ABSTAIN,
        )

        trusted = append_entry(
            (),
            bundle=first,
            published_at=500,
        )

        candidate = append_entry(
            trusted,
            bundle=second,
            published_at=501,
        )

        validate_extension(
            trusted,
            candidate,
        )

        rewritten = deepcopy(
            list(
                candidate
            )
        )

        rewritten[0][
            "published_at"
        ] = 499

        with self.assertRaises(
            AuditError
        ):
            validate_extension(
                trusted,
                rewritten,
            )


if __name__ == "__main__":
    unittest.main()
