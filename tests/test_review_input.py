from __future__ import annotations

from copy import deepcopy
import ast
import hashlib
import inspect
from pathlib import Path
import unittest


class ReviewInputTests(unittest.TestCase):
    @staticmethod
    def _module():
        import spec_model.review_input as review_input

        return review_input

    @staticmethod
    def _input_bytes() -> bytes:
        return (
            b'{"evidence":"exact-reviewed-bytes",'
            b'"mission":"mission-42"}'
        )

    @staticmethod
    def _derivation_bytes() -> bytes:
        return (
            b"method: semantic-confidence\n"
            b"version: 1.0.0\n"
            b"rule: evaluate supplied review input "
            b"under the documented method\n"
        )

    @classmethod
    def _binding(
        cls,
        *,
        decision: str = "COMMIT",
        confidence_bps: int = 8_000,
    ):
        module = cls._module()

        return module.review_input_binding(
            decision=decision,
            confidence_bps=confidence_bps,
            review_input_bytes=cls._input_bytes(),
            derivation_method="semantic-confidence",
            derivation_version="1.0.0",
            derivation_bytes=cls._derivation_bytes(),
        )

    def test_public_surface_is_explicit_and_has_no_defaults(self):
        module = self._module()

        self.assertEqual(
            module.REVIEW_INPUT_SCHEMA,
            "commit-review-confidence-input-v1",
        )

        self.assertEqual(
            module.PROVENANCE_SCOPE,
            "REPRODUCIBILITY_ONLY",
        )

        self.assertEqual(
            module.AUTHENTICITY,
            "UNVERIFIED",
        )

        self.assertTrue(
            issubclass(
                module.ReviewInputError,
                ValueError,
            )
        )

        signature = inspect.signature(
            module.review_input_binding
        )

        self.assertEqual(
            list(signature.parameters),
            [
                "decision",
                "confidence_bps",
                "review_input_bytes",
                "derivation_method",
                "derivation_version",
                "derivation_bytes",
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

    def test_binding_shape_is_exact_and_truthfully_unverified(self):
        binding = self._binding()

        self.assertEqual(
            set(binding),
            {
                "schema",
                "decision",
                "confidence_bps",
                "review_input_sha256",
                "derivation_method",
                "derivation_version",
                "derivation_sha256",
                "provenance_scope",
                "authenticity",
            },
        )

        self.assertEqual(
            binding["schema"],
            "commit-review-confidence-input-v1",
        )

        self.assertEqual(
            binding["provenance_scope"],
            "REPRODUCIBILITY_ONLY",
        )

        self.assertEqual(
            binding["authenticity"],
            "UNVERIFIED",
        )

    def test_exact_review_input_bytes_are_hash_bound(self):
        binding = self._binding()

        expected = hashlib.sha256(
            self._input_bytes()
        ).hexdigest()

        self.assertEqual(
            binding["review_input_sha256"],
            expected,
        )

        changed = self._module().review_input_binding(
            decision="COMMIT",
            confidence_bps=8_000,
            review_input_bytes=(
                self._input_bytes()
                + b"\n"
            ),
            derivation_method="semantic-confidence",
            derivation_version="1.0.0",
            derivation_bytes=self._derivation_bytes(),
        )

        self.assertNotEqual(
            binding["review_input_sha256"],
            changed["review_input_sha256"],
        )

    def test_exact_derivation_bytes_are_hash_bound(self):
        binding = self._binding()

        expected = hashlib.sha256(
            self._derivation_bytes()
        ).hexdigest()

        self.assertEqual(
            binding["derivation_sha256"],
            expected,
        )

        changed = self._module().review_input_binding(
            decision="COMMIT",
            confidence_bps=8_000,
            review_input_bytes=self._input_bytes(),
            derivation_method="semantic-confidence",
            derivation_version="1.0.0",
            derivation_bytes=(
                self._derivation_bytes()
                + b"\n"
            ),
        )

        self.assertNotEqual(
            binding["derivation_sha256"],
            changed["derivation_sha256"],
        )

    def test_binding_is_deterministic(self):
        self.assertEqual(
            self._binding(),
            self._binding(),
        )

    def test_decision_domain_is_exactly_commit_abort(self):
        module = self._module()

        for decision in (
            "ABSTAIN",
            "POLICY_ABSTAIN",
            "commit",
            "abort",
            "",
            1,
            None,
        ):
            with self.subTest(
                decision=decision,
            ):
                with self.assertRaises(
                    module.ReviewInputError
                ):
                    module.review_input_binding(
                        decision=decision,
                        confidence_bps=8_000,
                        review_input_bytes=self._input_bytes(),
                        derivation_method="semantic-confidence",
                        derivation_version="1.0.0",
                        derivation_bytes=self._derivation_bytes(),
                    )

        for decision in (
            "COMMIT",
            "ABORT",
        ):
            with self.subTest(
                decision=decision,
            ):
                binding = module.review_input_binding(
                    decision=decision,
                    confidence_bps=8_000,
                    review_input_bytes=self._input_bytes(),
                    derivation_method="semantic-confidence",
                    derivation_version="1.0.0",
                    derivation_bytes=self._derivation_bytes(),
                )

                self.assertEqual(
                    binding["decision"],
                    decision,
                )

    def test_confidence_domain_is_strict_basis_points(self):
        module = self._module()

        for value in (
            True,
            False,
            -1,
            10_001,
            1.0,
            "8000",
            None,
        ):
            with self.subTest(
                confidence_bps=value,
            ):
                with self.assertRaises(
                    module.ReviewInputError
                ):
                    module.review_input_binding(
                        decision="COMMIT",
                        confidence_bps=value,
                        review_input_bytes=self._input_bytes(),
                        derivation_method="semantic-confidence",
                        derivation_version="1.0.0",
                        derivation_bytes=self._derivation_bytes(),
                    )

        for value in (
            0,
            10_000,
        ):
            with self.subTest(
                confidence_bps=value,
            ):
                binding = module.review_input_binding(
                    decision="ABORT",
                    confidence_bps=value,
                    review_input_bytes=self._input_bytes(),
                    derivation_method="semantic-confidence",
                    derivation_version="1.0.0",
                    derivation_bytes=self._derivation_bytes(),
                )

                self.assertEqual(
                    binding["confidence_bps"],
                    value,
                )

    def test_material_inputs_require_exact_nonempty_bytes(self):
        module = self._module()

        vectors = (
            (
                "review_input_bytes",
                b"",
            ),
            (
                "review_input_bytes",
                bytearray(b"x"),
            ),
            (
                "review_input_bytes",
                "x",
            ),
            (
                "derivation_bytes",
                b"",
            ),
            (
                "derivation_bytes",
                bytearray(b"x"),
            ),
            (
                "derivation_bytes",
                "x",
            ),
        )

        for field, value in vectors:
            with self.subTest(
                field=field,
                value=value,
            ):
                kwargs = {
                    "decision": "COMMIT",
                    "confidence_bps": 8_000,
                    "review_input_bytes": self._input_bytes(),
                    "derivation_method": "semantic-confidence",
                    "derivation_version": "1.0.0",
                    "derivation_bytes": self._derivation_bytes(),
                }

                kwargs[
                    field
                ] = value

                with self.assertRaises(
                    module.ReviewInputError
                ):
                    module.review_input_binding(
                        **kwargs
                    )

    def test_derivation_method_and_version_are_strict_labels(self):
        module = self._module()

        for field in (
            "derivation_method",
            "derivation_version",
        ):
            for value in (
                "",
                " leading",
                "trailing ",
                "has\nnewline",
                "é",
                1,
                None,
            ):
                with self.subTest(
                    field=field,
                    value=value,
                ):
                    kwargs = {
                        "decision": "COMMIT",
                        "confidence_bps": 8_000,
                        "review_input_bytes": self._input_bytes(),
                        "derivation_method": "semantic-confidence",
                        "derivation_version": "1.0.0",
                        "derivation_bytes": self._derivation_bytes(),
                    }

                    kwargs[
                        field
                    ] = value

                    with self.assertRaises(
                        module.ReviewInputError
                    ):
                        module.review_input_binding(
                            **kwargs
                        )

    def test_validate_binding_rejects_shape_schema_scope_authenticity_and_bad_hash_format(
        self,
    ):
        module = self._module()

        valid = self._binding()

        validated = module.validate_review_input_binding(
            valid
        )

        self.assertEqual(
            validated,
            valid,
        )

        missing = deepcopy(
            valid
        )

        missing.pop(
            "review_input_sha256"
        )

        extra = {
            **valid,
            "reviewer_id": "fake",
        }

        wrong_schema = {
            **valid,
            "schema": "wrong",
        }

        malformed_input_hash = {
            **valid,
            "review_input_sha256": (
                "00" * 31
            ),
        }

        malformed_derivation_hash = {
            **valid,
            "derivation_sha256": (
                "not-a-sha256"
            ),
        }

        wrong_scope = {
            **valid,
            "provenance_scope": "AUTHENTICATED",
        }

        wrong_authenticity = {
            **valid,
            "authenticity": "VERIFIED",
        }

        for forged in (
            missing,
            extra,
            wrong_schema,
            malformed_input_hash,
            malformed_derivation_hash,
            wrong_scope,
            wrong_authenticity,
        ):
            with self.subTest(
                forged=forged,
            ):
                with self.assertRaises(
                    module.ReviewInputError
                ):
                    module.validate_review_input_binding(
                        forged
                    )

    def test_structural_validation_does_not_claim_material_hash_match(self):
        module = self._module()

        valid = self._binding()

        substituted = {
            **valid,
            "review_input_sha256": (
                "00" * 32
            ),
            "derivation_sha256": (
                "11" * 32
            ),
        }

        validated = (
            module.validate_review_input_binding(
                substituted
            )
        )

        self.assertEqual(
            validated,
            substituted,
        )

        with self.assertRaises(
            module.ReviewInputError
        ):
            module.verify_review_input_material(
                substituted,
                review_input_bytes=self._input_bytes(),
                derivation_bytes=self._derivation_bytes(),
            )

    def test_verify_material_accepts_exact_bytes(self):
        module = self._module()

        binding = self._binding()

        validated = (
            module.verify_review_input_material(
                binding,
                review_input_bytes=self._input_bytes(),
                derivation_bytes=self._derivation_bytes(),
            )
        )

        self.assertEqual(
            validated,
            binding,
        )

    def test_verify_material_rejects_input_substitution(self):
        module = self._module()

        with self.assertRaises(
            module.ReviewInputError
        ):
            module.verify_review_input_material(
                self._binding(),
                review_input_bytes=(
                    self._input_bytes()
                    + b"x"
                ),
                derivation_bytes=self._derivation_bytes(),
            )

    def test_verify_material_rejects_derivation_substitution(self):
        module = self._module()

        with self.assertRaises(
            module.ReviewInputError
        ):
            module.verify_review_input_material(
                self._binding(),
                review_input_bytes=self._input_bytes(),
                derivation_bytes=(
                    self._derivation_bytes()
                    + b"x"
                ),
            )

    def test_module_is_pure_and_cannot_claim_external_authority(self):
        module = self._module()

        source_path = Path(
            inspect.getsourcefile(
                module
            )
        )

        source = source_path.read_text()
        lower = source.lower()

        tree = ast.parse(
            source
        )

        imported_roots = set()

        for node in ast.walk(
            tree
        ):
            if isinstance(
                node,
                ast.Import,
            ):
                for alias in node.names:
                    imported_roots.add(
                        alias.name.split(
                            "."
                        )[0]
                    )

            elif isinstance(
                node,
                ast.ImportFrom,
            ):
                if node.module:
                    imported_roots.add(
                        node.module.split(
                            "."
                        )[0]
                    )

        forbidden_imports = {
            "requests",
            "httpx",
            "urllib",
            "socket",
            "subprocess",
            "genlayer",
            "random",
            "secrets",
            "uuid",
            "datetime",
            "time",
        }

        self.assertTrue(
            imported_roots.isdisjoint(
                forbidden_imports
            )
        )

        for forbidden_claim in (
            "reviewer_id",
            "producer_id",
            "authority_id",
            "issuer_id",
            "public_key",
            "signing_key",
            "signature",
            "trusted_reviewer",
        ):
            self.assertNotIn(
                forbidden_claim,
                lower,
            )

        self.assertEqual(
            module.PROVENANCE_SCOPE,
            "REPRODUCIBILITY_ONLY",
        )

        self.assertEqual(
            module.AUTHENTICITY,
            "UNVERIFIED",
        )


if __name__ == "__main__":
    unittest.main()
