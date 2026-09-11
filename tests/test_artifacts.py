import unittest

from spec_model.canonical import digest, encode
from spec_model.review_runner import ReviewRun, canonical_result


class ArtifactBundleTests(unittest.TestCase):
    def _run(self) -> ReviewRun:
        return ReviewRun(
            mission_id="artifact-mission",
            mission_version=7,
            effect_root="11" * 32,
            sealed_evidence_root="22" * 32,
            active_evidence_root="33" * 32,
        )

    def _inputs(self) -> dict[str, object]:
        return {
            "review_result": canonical_result(self._run()),
            "contract_source_sha256": "44" * 32,
            "runtime_archive_sha256": "55" * 32,
        }

    def test_bundle_schema_and_complete_identity_surface(self):
        from spec_model.artifacts import artifact_bundle

        bundle = artifact_bundle(**self._inputs())

        self.assertEqual(bundle["schema"], "commit-review-artifact-bundle-v1")
        self.assertEqual(
            bundle["review_result"],
            self._inputs()["review_result"],
        )
        self.assertEqual(
            bundle["contract_source_sha256"],
            "44" * 32,
        )
        self.assertEqual(
            bundle["runtime_archive_sha256"],
            "55" * 32,
        )
        self.assertEqual(
            set(bundle),
            {
                "schema",
                "review_result",
                "contract_source_sha256",
                "runtime_archive_sha256",
            },
        )

    def test_bundle_digest_reuses_canonical_protocol_encoding(self):
        from spec_model.artifacts import artifact_bundle, bundle_digest

        bundle = artifact_bundle(**self._inputs())

        self.assertEqual(
            bundle_digest(bundle),
            digest("review_artifact_bundle", bundle),
        )
        self.assertEqual(
            len(bundle_digest(bundle)),
            64,
        )

    def test_bundle_encoding_is_order_independent(self):
        from spec_model.artifacts import artifact_bundle, bundle_bytes

        bundle = artifact_bundle(**self._inputs())
        reordered = dict(reversed(list(bundle.items())))

        self.assertEqual(
            bundle_bytes(bundle),
            bundle_bytes(reordered),
        )
        self.assertEqual(
            bundle_bytes(bundle),
            encode("review_artifact_bundle", bundle),
        )

    def test_review_result_substitution_changes_bundle_digest(self):
        from spec_model.artifacts import artifact_bundle, bundle_digest

        original_inputs = self._inputs()
        original = artifact_bundle(**original_inputs)

        base_run = self._run()

        changed_run = ReviewRun(
            mission_id="artifact-mission-substituted",
            mission_version=base_run.mission_version,
            effect_root=base_run.effect_root,
            sealed_evidence_root=base_run.sealed_evidence_root,
            active_evidence_root=base_run.active_evidence_root,
        )

        changed_inputs = self._inputs()
        changed_inputs["review_result"] = canonical_result(changed_run)

        changed = artifact_bundle(**changed_inputs)

        self.assertNotEqual(
            original["review_result"]["run_id"],
            changed["review_result"]["run_id"],
        )
        self.assertNotEqual(
            bundle_digest(original),
            bundle_digest(changed),
        )

    def test_contract_source_substitution_changes_bundle_digest(self):
        from spec_model.artifacts import artifact_bundle, bundle_digest

        original = artifact_bundle(**self._inputs())

        changed_inputs = self._inputs()
        changed_inputs["contract_source_sha256"] = "66" * 32

        changed = artifact_bundle(**changed_inputs)

        self.assertNotEqual(
            bundle_digest(original),
            bundle_digest(changed),
        )

    def test_runtime_substitution_changes_bundle_digest(self):
        from spec_model.artifacts import artifact_bundle, bundle_digest

        original = artifact_bundle(**self._inputs())

        changed_inputs = self._inputs()
        changed_inputs["runtime_archive_sha256"] = "77" * 32

        changed = artifact_bundle(**changed_inputs)

        self.assertNotEqual(
            bundle_digest(original),
            bundle_digest(changed),
        )

    def test_invalid_hashes_are_rejected(self):
        from spec_model.artifacts import ArtifactError, artifact_bundle

        vectors = (
            {
                "contract_source_sha256": "44",
            },
            {
                "contract_source_sha256": "AA" * 32,
            },
            {
                "runtime_archive_sha256": "55",
            },
            {
                "runtime_archive_sha256": "BB" * 32,
            },
        )

        for change in vectors:
            with self.subTest(change=change):
                args = self._inputs()
                args.update(change)

                with self.assertRaises(ArtifactError):
                    artifact_bundle(**args)

    def test_invalid_review_result_is_rejected(self):
        from spec_model.artifacts import ArtifactError, artifact_bundle

        vectors = (
            None,
            [],
            {},
            {"schema": "wrong"},
            {
                **canonical_result(self._run()),
                "schema": "wrong",
            },
        )

        for value in vectors:
            with self.subTest(value=value):
                args = self._inputs()
                args["review_result"] = value

                with self.assertRaises(ArtifactError):
                    artifact_bundle(**args)

    def test_bundle_digest_rejects_schema_substitution(self):
        from spec_model.artifacts import ArtifactError, artifact_bundle, bundle_digest

        bundle = artifact_bundle(**self._inputs())
        changed = dict(bundle)
        changed["schema"] = "commit-review-artifact-bundle-v2"

        with self.assertRaises(ArtifactError):
            bundle_digest(changed)

    def test_bundle_rejects_extra_fields(self):
        from spec_model.artifacts import ArtifactError, artifact_bundle, bundle_digest

        bundle = artifact_bundle(**self._inputs())
        changed = dict(bundle)
        changed["unexpected"] = "not-allowed"

        with self.assertRaises(ArtifactError):
            bundle_digest(changed)

    def test_bundle_has_no_step5_audit_metadata(self):
        from spec_model.artifacts import artifact_bundle

        bundle = artifact_bundle(**self._inputs())

        for forbidden in (
            "previous_digest",
            "sequence",
            "published_at",
            "audit_log",
            "audit_entry",
        ):
            self.assertNotIn(forbidden, bundle)


    def test_fixed_bundle_digest_vector(self):
        from spec_model.artifacts import artifact_bundle, bundle_digest

        bundle = artifact_bundle(
            review_result=canonical_result(
                ReviewRun(
                    mission_id="step4-canonical-parity",
                    mission_version=11,
                    effect_root="11" * 32,
                    sealed_evidence_root="22" * 32,
                    active_evidence_root="33" * 32,
                )
            ),
            contract_source_sha256="44" * 32,
            runtime_archive_sha256="55" * 32,
        )

        self.assertEqual(
            bundle_digest(bundle),
            "97bfce94c70767df73395a9f34068be8a220b4fa97acec9ff646319c744fc675",
        )

if __name__ == "__main__":
    unittest.main()
