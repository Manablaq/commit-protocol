from __future__ import annotations

import ast
import inspect
from pathlib import Path
import unittest


class ConfidencePolicyTests(unittest.TestCase):
    @staticmethod
    def _policy():
        import spec_model.confidence_policy as policy

        return policy

    def test_surface_has_no_magic_threshold(self):
        policy = self._policy()

        self.assertEqual(
            policy.MAX_CONFIDENCE_BPS,
            10_000,
        )
        self.assertEqual(
            policy.DECISION_READY,
            "DECISION_READY",
        )
        self.assertEqual(
            policy.POLICY_ABSTAIN,
            "POLICY_ABSTAIN",
        )
        self.assertTrue(
            issubclass(
                policy.PolicyError,
                ValueError,
            )
        )

        signature = inspect.signature(
            policy.confidence_gate
        )

        self.assertEqual(
            list(signature.parameters),
            [
                "decision",
                "confidence_bps",
                "minimum_confidence_bps",
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

        for forbidden in (
            "DEFAULT_CONFIDENCE_BPS",
            "DEFAULT_MINIMUM_CONFIDENCE_BPS",
            "CONFIDENCE_THRESHOLD_BPS",
            "MINIMUM_CONFIDENCE_BPS",
        ):
            self.assertFalse(
                hasattr(policy, forbidden),
                forbidden,
            )

    def test_exact_threshold_is_decision_ready_for_both_decisions(self):
        policy = self._policy()

        for decision in (
            "COMMIT",
            "ABORT",
        ):
            with self.subTest(
                decision=decision,
            ):
                self.assertEqual(
                    policy.confidence_gate(
                        decision=decision,
                        confidence_bps=7_500,
                        minimum_confidence_bps=7_500,
                    ),
                    policy.DECISION_READY,
                )

    def test_above_threshold_is_decision_ready_for_both_decisions(self):
        policy = self._policy()

        for decision in (
            "COMMIT",
            "ABORT",
        ):
            with self.subTest(
                decision=decision,
            ):
                self.assertEqual(
                    policy.confidence_gate(
                        decision=decision,
                        confidence_bps=9_001,
                        minimum_confidence_bps=9_000,
                    ),
                    policy.DECISION_READY,
                )

    def test_below_threshold_policy_abstains_for_both_decisions(self):
        policy = self._policy()

        for decision in (
            "COMMIT",
            "ABORT",
        ):
            with self.subTest(
                decision=decision,
            ):
                self.assertEqual(
                    policy.confidence_gate(
                        decision=decision,
                        confidence_bps=8_999,
                        minimum_confidence_bps=9_000,
                    ),
                    policy.POLICY_ABSTAIN,
                )

    def test_explicit_zero_threshold_has_no_implicit_minimum(self):
        policy = self._policy()

        for decision in (
            "COMMIT",
            "ABORT",
        ):
            with self.subTest(
                decision=decision,
            ):
                self.assertEqual(
                    policy.confidence_gate(
                        decision=decision,
                        confidence_bps=0,
                        minimum_confidence_bps=0,
                    ),
                    policy.DECISION_READY,
                )

    def test_maximum_threshold_requires_maximum_confidence(self):
        policy = self._policy()

        for decision in (
            "COMMIT",
            "ABORT",
        ):
            with self.subTest(
                decision=decision,
                confidence_bps=10_000,
            ):
                self.assertEqual(
                    policy.confidence_gate(
                        decision=decision,
                        confidence_bps=10_000,
                        minimum_confidence_bps=10_000,
                    ),
                    policy.DECISION_READY,
                )

            with self.subTest(
                decision=decision,
                confidence_bps=9_999,
            ):
                self.assertEqual(
                    policy.confidence_gate(
                        decision=decision,
                        confidence_bps=9_999,
                        minimum_confidence_bps=10_000,
                    ),
                    policy.POLICY_ABSTAIN,
                )

    def test_invalid_decision_domain_is_rejected(self):
        policy = self._policy()

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
                    policy.PolicyError
                ):
                    policy.confidence_gate(
                        decision=decision,
                        confidence_bps=9_000,
                        minimum_confidence_bps=8_000,
                    )

    def test_invalid_confidence_bps_is_rejected(self):
        policy = self._policy()

        for value in (
            True,
            False,
            -1,
            10_001,
            1.0,
            "9000",
            None,
        ):
            with self.subTest(
                confidence_bps=value,
            ):
                with self.assertRaises(
                    policy.PolicyError
                ):
                    policy.confidence_gate(
                        decision="COMMIT",
                        confidence_bps=value,
                        minimum_confidence_bps=8_000,
                    )

    def test_invalid_minimum_confidence_bps_is_rejected(self):
        policy = self._policy()

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
                minimum_confidence_bps=value,
            ):
                with self.assertRaises(
                    policy.PolicyError
                ):
                    policy.confidence_gate(
                        decision="ABORT",
                        confidence_bps=9_000,
                        minimum_confidence_bps=value,
                    )

    def test_policy_module_is_pure_and_does_not_own_settlement(self):
        policy = self._policy()

        source = Path(
            inspect.getsourcefile(policy)
        ).read_text()

        tree = ast.parse(source)

        imports = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(
                    alias.name
                    for alias in node.names
                )
            elif isinstance(node, ast.ImportFrom):
                imports.append(
                    node.module or ""
                )

        for forbidden in (
            "time",
            "datetime",
            "random",
            "uuid",
            "secrets",
            "requests",
            "httpx",
            "urllib",
            "socket",
            "subprocess",
            "genlayer",
        ):
            for module in imports:
                self.assertFalse(
                    module == forbidden
                    or module.startswith(
                        forbidden + "."
                    ),
                    module,
                )

        lowered = source.lower()

        for forbidden in (
            "decision_nonce",
            "allocation",
            "settlement",
            "refund",
            "transfer",
            "policy_digest",
            "intent_digest",
        ):
            self.assertNotIn(
                forbidden,
                lowered,
            )


if __name__ == "__main__":
    unittest.main()
