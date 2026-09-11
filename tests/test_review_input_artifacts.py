from __future__ import annotations

from copy import deepcopy
import inspect
import unittest

from spec_model.artifacts import (
    ArtifactError,
    BUNDLE_SCHEMA,
    POLICY_BUNDLE_SCHEMA,
    artifact_bundle,
    bundle_digest,
    policy_artifact_bundle,
)
from spec_model.audit_log import (
    append_entry,
    validate_publications,
)
from spec_model.confidence_policy import (
    DECISION_READY,
    POLICY_ABSTAIN,
)
from spec_model.onchain import decision_nonce_v3
from spec_model.review_input import (
    AUTHENTICITY,
    PROVENANCE_SCOPE,
    REVIEW_INPUT_SCHEMA,
    review_input_binding,
)
from spec_model.review_runner import (
    ReviewRun,
    canonical_result,
    step,
)


CONTRACT_SHA = "44" * 32
RUNTIME_SHA = "55" * 32


class ReviewInputArtifactTests(unittest.TestCase):
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

    @staticmethod
    def _review_input(
        *,
        decision: str,
        confidence_bps: int,
        suffix: bytes = b"",
        derivation_version: str = "1.0.0",
    ) -> dict[str, object]:
        return review_input_binding(
            decision=decision,
            confidence_bps=confidence_bps,
            review_input_bytes=(
                b'{"mission":"review-input-artifact",'
                b'"evidence":"exact"}'
                + suffix
            ),
            derivation_method=(
                "semantic-confidence"
            ),
            derivation_version=(
                derivation_version
            ),
            derivation_bytes=(
                b"method: semantic-confidence\n"
                b"version: "
                + derivation_version.encode(
                    "ascii"
                )
                + b"\n"
            ),
        )

    @classmethod
    def _v3_bundle(
        cls,
        run: ReviewRun,
        *,
        decision: str,
        confidence_bps: int,
        minimum_confidence_bps: int,
        outcome: str,
        review_input: dict[str, object] | None = None,
    ) -> dict[str, object]:
        artifacts = cls._artifacts()

        if review_input is None:
            review_input = cls._review_input(
                decision=decision,
                confidence_bps=confidence_bps,
            )

        return (
            artifacts.review_input_policy_artifact_bundle(
                review_result=canonical_result(
                    run
                ),
                policy_assessment=cls._assessment(
                    decision=decision,
                    confidence_bps=confidence_bps,
                    minimum_confidence_bps=(
                        minimum_confidence_bps
                    ),
                    outcome=outcome,
                ),
                review_input_binding=review_input,
                contract_source_sha256=(
                    CONTRACT_SHA
                ),
                runtime_archive_sha256=(
                    RUNTIME_SHA
                ),
            )
        )

    def test_v1_v2_and_review_input_contract_remain_supported(self):
        artifacts = self._artifacts()

        ready = self._ready(
            "v1-v2-v3-compat-control"
        )

        v1 = artifact_bundle(
            review_result=canonical_result(
                ready
            ),
            contract_source_sha256=CONTRACT_SHA,
            runtime_archive_sha256=RUNTIME_SHA,
        )

        v2 = policy_artifact_bundle(
            review_result=canonical_result(
                ready
            ),
            policy_assessment=self._assessment(
                decision="COMMIT",
                confidence_bps=7_999,
                minimum_confidence_bps=8_000,
                outcome=POLICY_ABSTAIN,
            ),
            contract_source_sha256=CONTRACT_SHA,
            runtime_archive_sha256=RUNTIME_SHA,
        )

        binding = self._review_input(
            decision="COMMIT",
            confidence_bps=7_999,
        )

        self.assertEqual(
            v1["schema"],
            BUNDLE_SCHEMA,
        )

        self.assertEqual(
            v2["schema"],
            POLICY_BUNDLE_SCHEMA,
        )

        self.assertRegex(
            bundle_digest(
                v1
            ),
            r"^[0-9a-f]{64}$",
        )

        self.assertRegex(
            bundle_digest(
                v2
            ),
            r"^[0-9a-f]{64}$",
        )

        self.assertEqual(
            binding["schema"],
            REVIEW_INPUT_SCHEMA,
        )

        self.assertEqual(
            binding["provenance_scope"],
            PROVENANCE_SCOPE,
        )

        self.assertEqual(
            binding["authenticity"],
            AUTHENTICITY,
        )

        self.assertNotIn(
            "minimum_confidence_bps",
            binding,
        )


    def test_v3_public_surface_is_versioned_and_explicit(self):
        artifacts = self._artifacts()

        self.assertEqual(
            artifacts.REPRODUCIBLE_POLICY_BUNDLE_SCHEMA,
            "commit-review-artifact-bundle-v3",
        )

        signature = inspect.signature(
            artifacts.review_input_policy_artifact_bundle
        )

        self.assertEqual(
            list(signature.parameters),
            [
                "review_result",
                "policy_assessment",
                "review_input_binding",
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

    def test_v3_policy_abstain_accepts_matching_review_input(self):
        artifacts = self._artifacts()

        bundle = self._v3_bundle(
            self._ready(
                "v3-abstain"
            ),
            decision="COMMIT",
            confidence_bps=7_999,
            minimum_confidence_bps=8_000,
            outcome=POLICY_ABSTAIN,
        )

        self.assertEqual(
            bundle["schema"],
            artifacts.REPRODUCIBLE_POLICY_BUNDLE_SCHEMA,
        )

        self.assertEqual(
            bundle[
                "review_input_binding"
            ][
                "decision"
            ],
            bundle[
                "policy_assessment"
            ][
                "decision"
            ],
        )

        self.assertEqual(
            bundle[
                "review_input_binding"
            ][
                "confidence_bps"
            ],
            bundle[
                "policy_assessment"
            ][
                "confidence_bps"
            ],
        )

        self.assertEqual(
            bundle[
                "review_input_binding"
            ][
                "provenance_scope"
            ],
            "REPRODUCIBILITY_ONLY",
        )

        self.assertEqual(
            bundle[
                "review_input_binding"
            ][
                "authenticity"
            ],
            "UNVERIFIED",
        )

    def test_v3_decision_ready_accepts_matching_review_input(self):
        bundle = self._v3_bundle(
            self._decided(
                "v3-ready",
                "ABORT",
            ),
            decision="ABORT",
            confidence_bps=9_000,
            minimum_confidence_bps=8_000,
            outcome=DECISION_READY,
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
            "ABORT",
        )

        self.assertEqual(
            bundle[
                "review_input_binding"
            ][
                "decision"
            ],
            "ABORT",
        )

    def test_v3_rejects_review_input_decision_mismatch(self):
        artifacts = self._artifacts()

        binding = self._review_input(
            decision="ABORT",
            confidence_bps=8_000,
        )

        with self.assertRaises(
            ArtifactError
        ):
            self._v3_bundle(
                self._decided(
                    "v3-decision-mismatch",
                    "COMMIT",
                ),
                decision="COMMIT",
                confidence_bps=8_000,
                minimum_confidence_bps=8_000,
                outcome=DECISION_READY,
                review_input=binding,
            )

    def test_v3_rejects_review_input_confidence_mismatch(self):
        artifacts = self._artifacts()

        binding = self._review_input(
            decision="COMMIT",
            confidence_bps=7_999,
        )

        with self.assertRaises(
            ArtifactError
        ):
            self._v3_bundle(
                self._decided(
                    "v3-confidence-mismatch",
                    "COMMIT",
                ),
                decision="COMMIT",
                confidence_bps=8_000,
                minimum_confidence_bps=8_000,
                outcome=DECISION_READY,
                review_input=binding,
            )

    def test_v3_rejects_forged_review_input_scope_or_authenticity(self):
        artifacts = self._artifacts()

        valid = self._review_input(
            decision="COMMIT",
            confidence_bps=7_999,
        )

        forged_scope = {
            **valid,
            "provenance_scope": "AUTHENTICATED",
        }

        forged_authenticity = {
            **valid,
            "authenticity": "VERIFIED",
        }

        for binding in (
            forged_scope,
            forged_authenticity,
        ):
            with self.subTest(
                binding=binding,
            ):
                with self.assertRaises(
                    ArtifactError
                ):
                    self._v3_bundle(
                        self._ready(
                            "v3-forged-provenance"
                        ),
                        decision="COMMIT",
                        confidence_bps=7_999,
                        minimum_confidence_bps=8_000,
                        outcome=POLICY_ABSTAIN,
                        review_input=binding,
                    )

    def test_v3_digest_binds_review_input_and_derivation_material_hashes(self):
        first = self._v3_bundle(
            self._ready(
                "v3-digest-binding"
            ),
            decision="COMMIT",
            confidence_bps=7_999,
            minimum_confidence_bps=8_000,
            outcome=POLICY_ABSTAIN,
            review_input=self._review_input(
                decision="COMMIT",
                confidence_bps=7_999,
                suffix=b"-one",
            ),
        )

        second = self._v3_bundle(
            self._ready(
                "v3-digest-binding"
            ),
            decision="COMMIT",
            confidence_bps=7_999,
            minimum_confidence_bps=8_000,
            outcome=POLICY_ABSTAIN,
            review_input=self._review_input(
                decision="COMMIT",
                confidence_bps=7_999,
                suffix=b"-two",
            ),
        )

        third = self._v3_bundle(
            self._ready(
                "v3-digest-binding"
            ),
            decision="COMMIT",
            confidence_bps=7_999,
            minimum_confidence_bps=8_000,
            outcome=POLICY_ABSTAIN,
            review_input=self._review_input(
                decision="COMMIT",
                confidence_bps=7_999,
                suffix=b"-two",
                derivation_version="1.0.1",
            ),
        )

        self.assertNotEqual(
            first[
                "review_input_binding"
            ][
                "review_input_sha256"
            ],
            second[
                "review_input_binding"
            ][
                "review_input_sha256"
            ],
        )

        self.assertEqual(
            first[
                "review_input_binding"
            ][
                "derivation_sha256"
            ],
            second[
                "review_input_binding"
            ][
                "derivation_sha256"
            ],
        )

        self.assertEqual(
            second[
                "review_input_binding"
            ][
                "review_input_sha256"
            ],
            third[
                "review_input_binding"
            ][
                "review_input_sha256"
            ],
        )

        self.assertNotEqual(
            second[
                "review_input_binding"
            ][
                "derivation_sha256"
            ],
            third[
                "review_input_binding"
            ][
                "derivation_sha256"
            ],
        )

        run_ids = {
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
            third[
                "review_result"
            ][
                "run_id"
            ],
        }

        self.assertEqual(
            len(
                run_ids
            ),
            1,
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

    def test_v3_snapshots_review_input_binding(self):
        binding = self._review_input(
            decision="COMMIT",
            confidence_bps=7_999,
        )

        original_input_hash = (
            binding[
                "review_input_sha256"
            ]
        )

        bundle = self._v3_bundle(
            self._ready(
                "v3-snapshot"
            ),
            decision="COMMIT",
            confidence_bps=7_999,
            minimum_confidence_bps=8_000,
            outcome=POLICY_ABSTAIN,
            review_input=binding,
        )

        binding[
            "review_input_sha256"
        ] = "00" * 32

        self.assertEqual(
            bundle[
                "review_input_binding"
            ][
                "review_input_sha256"
            ],
            original_input_hash,
        )

    def test_v3_does_not_rederive_run_identity(self):
        run = self._ready(
            "v3-run-id-stability"
        )

        expected = canonical_result(
            run
        )

        bundle = self._v3_bundle(
            run,
            decision="ABORT",
            confidence_bps=6_000,
            minimum_confidence_bps=7_000,
            outcome=POLICY_ABSTAIN,
        )

        self.assertEqual(
            bundle[
                "review_result"
            ],
            expected,
        )

        self.assertEqual(
            bundle[
                "review_result"
            ][
                "run_id"
            ],
            run.run_id,
        )

    def test_v3_is_compatible_with_existing_audit_schema(self):
        bundle = self._v3_bundle(
            self._ready(
                "v3-audit"
            ),
            decision="COMMIT",
            confidence_bps=7_999,
            minimum_confidence_bps=8_000,
            outcome=POLICY_ABSTAIN,
        )

        log = append_entry(
            (),
            bundle=bundle,
            published_at=1234,
        )

        validate_publications(
            log,
            (bundle,),
        )

        self.assertEqual(
            len(
                log
            ),
            1,
        )

        self.assertEqual(
            log[0][
                "run_id"
            ],
            bundle[
                "review_result"
            ][
                "run_id"
            ],
        )

    def test_v2_v3_schema_substitution_is_rejected(self):
        artifacts = self._artifacts()

        ready = self._ready(
            "v2-v3-schema-confusion"
        )

        v2 = policy_artifact_bundle(
            review_result=canonical_result(
                ready
            ),
            policy_assessment=self._assessment(
                decision="COMMIT",
                confidence_bps=7_999,
                minimum_confidence_bps=8_000,
                outcome=POLICY_ABSTAIN,
            ),
            contract_source_sha256=CONTRACT_SHA,
            runtime_archive_sha256=RUNTIME_SHA,
        )

        forged = deepcopy(
            v2
        )

        forged[
            "schema"
        ] = (
            artifacts.REPRODUCIBLE_POLICY_BUNDLE_SCHEMA
        )

        with self.assertRaises(
            ArtifactError
        ):
            bundle_digest(
                forged
            )


if __name__ == "__main__":
    unittest.main()
