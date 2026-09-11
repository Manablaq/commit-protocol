from copy import deepcopy
import unittest

from spec_model.artifacts import artifact_bundle, bundle_digest
from spec_model.review_runner import ReviewRun, canonical_result, step


class AuditLogTests(unittest.TestCase):
    def _run(self) -> ReviewRun:
        return ReviewRun(
            mission_id="audit-mission",
            mission_version=23,
            effect_root="11" * 32,
            sealed_evidence_root="22" * 32,
            active_evidence_root="33" * 32,
        )

    def _bundle(self, run=None):
        if run is None:
            run = self._run()

        return artifact_bundle(
            review_result=canonical_result(run),
            contract_source_sha256="44" * 32,
            runtime_archive_sha256="55" * 32,
        )

    def test_first_entry_derives_existing_run_and_bundle_identities(self):
        from spec_model.audit_log import (
            GENESIS_PREVIOUS_DIGEST,
            append_entry,
        )

        bundle = self._bundle()

        log = append_entry(
            (),
            bundle=bundle,
            published_at=100,
        )

        self.assertEqual(len(log), 1)

        entry = log[0]

        self.assertEqual(
            set(entry),
            {
                "schema",
                "sequence",
                "previous_digest",
                "published_at",
                "run_id",
                "bundle_digest",
            },
        )

        self.assertEqual(
            entry["schema"],
            "commit-review-audit-entry-v1",
        )
        self.assertEqual(entry["sequence"], 0)
        self.assertEqual(
            entry["previous_digest"],
            GENESIS_PREVIOUS_DIGEST,
        )
        self.assertEqual(entry["published_at"], 100)
        self.assertEqual(
            entry["run_id"],
            bundle["review_result"]["run_id"],
        )
        self.assertEqual(
            entry["bundle_digest"],
            bundle_digest(bundle),
        )

    def test_entry_digest_reuses_canonical_protocol_encoding(self):
        from spec_model.audit_log import (
            append_entry,
            entry_digest,
        )
        from spec_model.canonical import digest

        entry = append_entry(
            (),
            bundle=self._bundle(),
            published_at=100,
        )[0]

        self.assertEqual(
            entry_digest(entry),
            digest("review_audit_entry", entry),
        )
        self.assertEqual(len(entry_digest(entry)), 64)

    def test_append_links_previous_digest_and_sequence(self):
        from spec_model.audit_log import (
            append_entry,
            entry_digest,
            validate_log,
        )

        first_bundle = self._bundle()

        first = append_entry(
            (),
            bundle=first_bundle,
            published_at=100,
        )

        second_bundle = self._bundle(
            ReviewRun(
                mission_id="audit-mission-2",
                mission_version=24,
                effect_root="11" * 32,
                sealed_evidence_root="22" * 32,
                active_evidence_root="33" * 32,
            )
        )

        second = append_entry(
            first,
            bundle=second_bundle,
            published_at=101,
        )

        self.assertEqual(len(second), 2)
        self.assertEqual(second[0]["sequence"], 0)
        self.assertEqual(second[1]["sequence"], 1)
        self.assertEqual(
            second[1]["previous_digest"],
            entry_digest(second[0]),
        )

        validate_log(second)

    def test_same_run_identity_can_publish_multiple_phase_bundles(self):
        from spec_model.audit_log import (
            append_entry,
            validate_log,
        )

        created = self._run()
        running = step(created, "start")

        created_bundle = self._bundle(created)
        running_bundle = self._bundle(running)

        self.assertEqual(
            created_bundle["review_result"]["run_id"],
            running_bundle["review_result"]["run_id"],
        )

        self.assertNotEqual(
            bundle_digest(created_bundle),
            bundle_digest(running_bundle),
        )

        log = append_entry(
            (),
            bundle=created_bundle,
            published_at=100,
        )

        log = append_entry(
            log,
            bundle=running_bundle,
            published_at=101,
        )

        self.assertEqual(
            log[0]["run_id"],
            log[1]["run_id"],
        )
        self.assertNotEqual(
            log[0]["bundle_digest"],
            log[1]["bundle_digest"],
        )

        validate_log(log)

    def test_validate_log_rejects_tampered_prior_entry(self):
        from spec_model.audit_log import (
            AuditError,
            append_entry,
            validate_log,
        )

        first = append_entry(
            (),
            bundle=self._bundle(),
            published_at=100,
        )

        second = append_entry(
            first,
            bundle=self._bundle(
                ReviewRun(
                    mission_id="tamper-second",
                    mission_version=25,
                    effect_root="11" * 32,
                    sealed_evidence_root="22" * 32,
                    active_evidence_root="33" * 32,
                )
            ),
            published_at=101,
        )

        vectors = {}

        candidate = deepcopy(second)
        candidate[0]["run_id"] = "99" * 32
        vectors["run_id"] = candidate

        candidate = deepcopy(second)
        candidate[0]["bundle_digest"] = "88" * 32
        vectors["bundle_digest"] = candidate

        candidate = deepcopy(second)
        candidate[0]["sequence"] = 7
        vectors["sequence"] = candidate

        candidate = deepcopy(second)
        candidate[0]["published_at"] = 99
        vectors["published_at"] = candidate

        for name, candidate in vectors.items():
            with self.subTest(name=name):
                with self.assertRaises(AuditError):
                    validate_log(candidate)

    def test_validate_log_rejects_broken_previous_digest(self):
        from spec_model.audit_log import (
            AuditError,
            append_entry,
            validate_log,
        )

        first = append_entry(
            (),
            bundle=self._bundle(),
            published_at=100,
        )

        log = append_entry(
            first,
            bundle=self._bundle(
                ReviewRun(
                    mission_id="broken-link",
                    mission_version=26,
                    effect_root="11" * 32,
                    sealed_evidence_root="22" * 32,
                    active_evidence_root="33" * 32,
                )
            ),
            published_at=101,
        )

        broken = deepcopy(log)
        broken[1]["previous_digest"] = "77" * 32

        with self.assertRaises(AuditError):
            validate_log(broken)

    def test_append_rejects_publication_time_regression(self):
        from spec_model.audit_log import (
            AuditError,
            append_entry,
        )

        first = append_entry(
            (),
            bundle=self._bundle(),
            published_at=100,
        )

        same_time = append_entry(
            first,
            bundle=self._bundle(
                ReviewRun(
                    mission_id="same-time",
                    mission_version=27,
                    effect_root="11" * 32,
                    sealed_evidence_root="22" * 32,
                    active_evidence_root="33" * 32,
                )
            ),
            published_at=100,
        )

        self.assertEqual(same_time[1]["published_at"], 100)

        with self.assertRaises(AuditError):
            append_entry(
                first,
                bundle=self._bundle(
                    ReviewRun(
                        mission_id="time-regression",
                        mission_version=28,
                        effect_root="11" * 32,
                        sealed_evidence_root="22" * 32,
                        active_evidence_root="33" * 32,
                    )
                ),
                published_at=99,
            )

    def test_log_rejects_wrong_schema_extra_fields_and_bad_hashes(self):
        from spec_model.audit_log import (
            AuditError,
            append_entry,
            validate_log,
        )

        base = append_entry(
            (),
            bundle=self._bundle(),
            published_at=100,
        )

        vectors = {}

        candidate = deepcopy(base)
        candidate[0]["schema"] = "commit-review-audit-entry-v2"
        vectors["schema"] = candidate

        candidate = deepcopy(base)
        candidate[0]["unexpected"] = "x"
        vectors["extra_field"] = candidate

        candidate = deepcopy(base)
        candidate[0]["run_id"] = "AA" * 32
        vectors["uppercase_run_id"] = candidate

        candidate = deepcopy(base)
        candidate[0]["bundle_digest"] = "aa"
        vectors["short_bundle_digest"] = candidate

        candidate = deepcopy(base)
        candidate[0]["previous_digest"] = "bb"
        vectors["short_previous_digest"] = candidate

        for name, candidate in vectors.items():
            with self.subTest(name=name):
                with self.assertRaises(AuditError):
                    validate_log(candidate)

    def test_append_rejects_invalid_bundle(self):
        from spec_model.audit_log import (
            AuditError,
            append_entry,
        )

        invalid = deepcopy(self._bundle())
        invalid["schema"] = "commit-review-artifact-bundle-v2"

        with self.assertRaises(AuditError):
            append_entry(
                (),
                bundle=invalid,
                published_at=100,
            )

    def test_append_snapshots_existing_log(self):
        from spec_model.audit_log import (
            append_entry,
            validate_log,
        )

        first = append_entry(
            (),
            bundle=self._bundle(),
            published_at=100,
        )

        second = append_entry(
            first,
            bundle=self._bundle(
                ReviewRun(
                    mission_id="snapshot-second",
                    mission_version=29,
                    effect_root="11" * 32,
                    sealed_evidence_root="22" * 32,
                    active_evidence_root="33" * 32,
                )
            ),
            published_at=101,
        )

        self.assertIsNot(second[0], first[0])

        first[0]["published_at"] = 999
        first[0]["run_id"] = "99" * 32

        self.assertEqual(second[0]["published_at"], 100)
        self.assertNotEqual(
            second[0]["run_id"],
            first[0]["run_id"],
        )

        validate_log(second)

    def test_audit_log_is_deterministic_and_has_no_step6_policy_metadata(self):
        from spec_model.audit_log import (
            append_entry,
            entry_digest,
        )

        bundle = self._bundle()

        one = append_entry(
            (),
            bundle=bundle,
            published_at=100,
        )

        two = append_entry(
            (),
            bundle=bundle,
            published_at=100,
        )

        self.assertEqual(one, two)
        self.assertEqual(
            entry_digest(one[0]),
            entry_digest(two[0]),
        )

        self.assertEqual(
            set(one[0]),
            {
                "schema",
                "sequence",
                "previous_digest",
                "published_at",
                "run_id",
                "bundle_digest",
            },
        )

        for forbidden in (
            "audit_run_id",
            "confidence",
            "confidence_bps",
            "abstain",
            "abstention",
            "threshold",
        ):
            self.assertNotIn(forbidden, one[0])


    def test_fixed_audit_entry_digest_vector(self):
        from spec_model.audit_log import append_entry, entry_digest

        bundle = artifact_bundle(
            review_result=canonical_result(
                ReviewRun(
                    mission_id="step5-canonical-parity",
                    mission_version=93,
                    effect_root="11" * 32,
                    sealed_evidence_root="22" * 32,
                    active_evidence_root="33" * 32,
                )
            ),
            contract_source_sha256="44" * 32,
            runtime_archive_sha256="55" * 32,
        )

        log = append_entry(
            (),
            bundle=bundle,
            published_at=123456789,
        )

        self.assertEqual(
            entry_digest(log[0]),
            "27b314251ebee5e23d48e93602f08e2bfaf6ec80a8b1d75121e20452d6fe8511",
        )

if __name__ == "__main__":
    unittest.main()
