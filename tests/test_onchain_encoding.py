import unittest

from spec_model.onchain import effect_leaf, effect_root, intent_digest


class OnchainEncodingTests(unittest.TestCase):
    def test_intent_digest_is_domain_separated_and_term_bound(self):
        args = dict(
            mission_id="mission-001",
            objective="Procure a verified sensor package",
            policy_digest="ab" * 32,
            budget=10,
            refund_beneficiary="0x" + "11" * 20,
            prepare_deadline=3_000_000_000,
            recovery_deadline=3_000_000_100,
        )
        original = intent_digest(**args)
        self.assertEqual(len(original), 64)
        for name, changed in (
            ("objective", "Procure a different package"),
            ("budget", 11),
            ("recovery_deadline", 3_000_000_101),
        ):
            with self.subTest(name=name):
                self.assertNotEqual(original, intent_digest(**{**args, name: changed}))

    def test_effect_leaf_binds_every_settlement_term(self):
        args = dict(
            effect_id="effect-001",
            effect_digest="cd" * 32,
            supplier="0x" + "12" * 20,
            beneficiary="0x" + "34" * 20,
            value=7,
            expiry=3_000_000_100,
        )
        original = effect_leaf(**args)
        self.assertEqual(len(original), 64)
        for name, changed in (("value", 8), ("expiry", 3_000_000_101)):
            with self.subTest(name=name):
                self.assertNotEqual(original, effect_leaf(**{**args, name: changed}))

    def test_effect_root_is_ordered_and_binds_the_complete_leaf(self):
        first = dict(
            effect_id="effect-001", digest="cd" * 32,
            supplier="0x" + "12" * 20, beneficiary="0x" + "34" * 20,
            value=7, expiry=3_000_000_100,
        )
        second = {**first, "effect_id": "effect-002", "value": 2}
        original = effect_root([first, second])
        self.assertNotEqual(original, effect_root([second, first]))
        self.assertNotEqual(original, effect_root([{**first, "value": 8}, second]))


if __name__ == "__main__":
    unittest.main()
