import json
import unittest

from spec_model.canonical import CanonicalError, digest, effect_body, encode


VALID = dict(
    domain_hash="11" * 32,
    mission_id="procurement-42",
    version=3,
    effect_id="supplier-a",
    recipient="0x" + "22" * 20,
    amount_wei=10**18,
    payload_hash="33" * 32,
    nonce=7,
    expires_at=2_000_000_000,
)


class CanonicalEncodingTests(unittest.TestCase):
    def test_fixed_vector(self):
        body = effect_body(**VALID)
        self.assertEqual(
            digest("effect", body),
            "44d4ca73b9e7fadce08113fb04c7b23fe99a1cbe10611ac3327b0fe2253981d6",
        )

    def test_order_is_irrelevant(self):
        body = effect_body(**VALID)
        reverse = dict(reversed(list(body.items())))
        self.assertEqual(encode("effect", body), encode("effect", reverse))

    def test_domain_separation(self):
        body = effect_body(**VALID)
        self.assertNotEqual(digest("effect", body), digest("receipt", body))

    def test_unicode_is_utf8_not_ascii_escaped(self):
        encoded = encode("evidence", {"issuer": "Café"})
        self.assertIn("Café".encode(), encoded)
        self.assertEqual(json.loads(encoded)["body"]["issuer"], "Café")

    def test_float_bytes_tuple_and_negative_int_rejected(self):
        for value in (1.0, b"x", (1,), -1, 2**256):
            with self.subTest(value=value):
                with self.assertRaises(CanonicalError):
                    encode("effect", {"value": value})

    def test_uppercase_hash_or_address_rejected(self):
        for change in (
            {"domain_hash": "AA" * 32},
            {"recipient": "0x" + "AB" * 20},
        ):
            args = {**VALID, **change}
            with self.assertRaises(CanonicalError):
                effect_body(**args)

    def test_type_and_size_bounds(self):
        with self.assertRaises(CanonicalError):
            encode("Effect", {})
        with self.assertRaises(CanonicalError):
            effect_body(**{**VALID, "mission_id": "x" * 97})


if __name__ == "__main__":
    unittest.main()
