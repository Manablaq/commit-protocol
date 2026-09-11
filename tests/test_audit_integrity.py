from copy import deepcopy
import unittest

from spec_model.artifacts import artifact_bundle
from spec_model.audit_log import (
    AUDIT_ENTRY_SCHEMA,
    AuditError,
    GENESIS_PREVIOUS_DIGEST,
    append_entry,
    entry_digest,
    validate_log,
)
from spec_model.review_runner import ReviewRun, canonical_result


class AuditIntegrityTests(unittest.TestCase):
    def _bundle(
        self,
        mission_id: str,
        mission_version: int,
    ):
        return artifact_bundle(
            review_result=canonical_result(
                ReviewRun(
                    mission_id=mission_id,
                    mission_version=mission_version,
                    effect_root="11" * 32,
                    sealed_evidence_root="22" * 32,
                    active_evidence_root="33" * 32,
                )
            ),
            contract_source_sha256="44" * 32,
            runtime_archive_sha256="55" * 32,
        )

    def _two_entry_log(self):
        first_bundle = self._bundle(
            "audit-integrity-first",
            60,
        )

        second_bundle = self._bundle(
            "audit-integrity-second",
            61,
        )

        log = append_entry(
            (),
            bundle=first_bundle,
            published_at=100,
        )

        log = append_entry(
            log,
            bundle=second_bundle,
            published_at=101,
        )

        return (
            log,
            (first_bundle, second_bundle),
        )

    def test_bundle_backed_validation_accepts_exact_publications(self):
        from spec_model.audit_log import validate_publications

        log, bundles = self._two_entry_log()

        validate_publications(
            log,
            bundles,
        )

    def test_bundle_backed_validation_rejects_fabricated_identities(self):
        from spec_model.audit_log import validate_publications

        log, bundles = self._two_entry_log()

        vectors = {}

        candidate = deepcopy(log)
        candidate[0]["run_id"] = "99" * 32
        candidate[1]["previous_digest"] = entry_digest(
            candidate[0]
        )
        vectors["fabricated_run_id"] = candidate

        candidate = deepcopy(log)
        candidate[0]["bundle_digest"] = "88" * 32
        candidate[1]["previous_digest"] = entry_digest(
            candidate[0]
        )
        vectors["fabricated_bundle_digest"] = candidate

        candidate = deepcopy(log)
        candidate[-1]["run_id"] = "77" * 32
        vectors["tampered_tail_run_id"] = candidate

        candidate = deepcopy(log)
        candidate[-1]["bundle_digest"] = "66" * 32
        vectors["tampered_tail_bundle_digest"] = candidate

        for name, candidate in vectors.items():
            with self.subTest(name=name):
                validate_log(candidate)

                with self.assertRaises(AuditError):
                    validate_publications(
                        candidate,
                        bundles,
                    )

    def test_bundle_backed_validation_rejects_cardinality_and_invalid_bundle(self):
        from spec_model.audit_log import validate_publications

        log, bundles = self._two_entry_log()

        with self.assertRaises(AuditError):
            validate_publications(
                log,
                bundles[:1],
            )

        invalid_bundles = list(bundles)
        invalid_bundles[1] = deepcopy(
            invalid_bundles[1]
        )
        invalid_bundles[1]["schema"] = (
            "commit-review-artifact-bundle-v2"
        )

        with self.assertRaises(AuditError):
            validate_publications(
                log,
                tuple(invalid_bundles),
            )

    def test_extension_validation_accepts_exact_prefix_and_append(self):
        from spec_model.audit_log import validate_extension

        first_bundle = self._bundle(
            "extension-first",
            62,
        )

        second_bundle = self._bundle(
            "extension-second",
            63,
        )

        trusted = append_entry(
            (),
            bundle=first_bundle,
            published_at=100,
        )

        extended = append_entry(
            trusted,
            bundle=second_bundle,
            published_at=101,
        )

        validate_extension(
            trusted,
            trusted,
        )

        validate_extension(
            trusted,
            extended,
        )

    def test_extension_validation_rejects_rewrite_and_rollback(self):
        from spec_model.audit_log import validate_extension

        log, _ = self._two_entry_log()

        rewritten = deepcopy(log)
        rewritten[0]["run_id"] = "91" * 32
        rewritten[0]["bundle_digest"] = "81" * 32
        rewritten[1]["previous_digest"] = entry_digest(
            rewritten[0]
        )

        validate_log(rewritten)

        with self.assertRaises(AuditError):
            validate_extension(
                log,
                rewritten,
            )

        with self.assertRaises(AuditError):
            validate_extension(
                log,
                log[:-1],
            )

    def test_extension_validation_rejects_tampered_trusted_tail_extension(self):
        from spec_model.audit_log import validate_extension

        trusted, _ = self._two_entry_log()

        tampered = deepcopy(trusted)
        tampered[-1]["run_id"] = "99" * 32
        tampered[-1]["bundle_digest"] = "88" * 32

        validate_log(tampered)

        candidate = append_entry(
            tampered,
            bundle=self._bundle(
                "tampered-tail-extension",
                64,
            ),
            published_at=102,
        )

        validate_log(candidate)

        with self.assertRaises(AuditError):
            validate_extension(
                trusted,
                candidate,
            )

    def test_u256_publication_boundary_is_normalized_to_audit_error(self):
        maximum = (1 << 256) - 1
        overflow = 1 << 256

        bundle = self._bundle(
            "u256-publication-boundary",
            65,
        )

        maximum_log = append_entry(
            (),
            bundle=bundle,
            published_at=maximum,
        )

        validate_log(maximum_log)
        entry_digest(maximum_log[0])

        overflow_entry = {
            "schema": AUDIT_ENTRY_SCHEMA,
            "sequence": 0,
            "previous_digest": GENESIS_PREVIOUS_DIGEST,
            "published_at": overflow,
            "run_id": "11" * 32,
            "bundle_digest": "22" * 32,
        }

        for name, operation in (
            (
                "validate_log",
                lambda: validate_log(
                    (overflow_entry,)
                ),
            ),
            (
                "entry_digest",
                lambda: entry_digest(
                    overflow_entry
                ),
            ),
            (
                "append_entry",
                lambda: append_entry(
                    (),
                    bundle=bundle,
                    published_at=overflow,
                ),
            ),
        ):
            with self.subTest(name=name):
                with self.assertRaises(AuditError):
                    operation()


if __name__ == "__main__":
    unittest.main()
