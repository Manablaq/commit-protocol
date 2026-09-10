import unittest

from spec_model.provenance import (
    ProvenanceError,
    evidence_root,
    url_matches_authority,
    validate_authority,
)


class ProvenanceTests(unittest.TestCase):
    HOST = "publisher-a.example"
    PREFIX = "/records"

    def test_exact_https_origin_and_path_boundary_are_required(self):
        self.assertTrue(url_matches_authority(
            "https://publisher-a.example/records/mission-001", self.HOST, self.PREFIX
        ))
        for url in (
            "http://publisher-a.example/records/mission-001",
            "https://publisher-a.example.evil/records/mission-001",
            "https://publisher-a.example/records-other/mission-001",
            "https://attacker@publisher-a.example/records/mission-001",
            "https://publisher-a.example:443/records/mission-001",
            "https://publisher-a.example/records/mission-001?redirect=evil",
            "https://publisher-a.example/records/../private",
            "https://publisher-a.example/records/%2e%2e/private",
        ):
            with self.subTest(url=url):
                self.assertFalse(url_matches_authority(url, self.HOST, self.PREFIX))

    def test_authority_registration_rejects_ambiguous_inputs(self):
        for args in (
            ("publisher", "Publisher.example", "/records"),
            ("publisher", "publisher .example", "/records"),
            ("publisher", "-publisher.example", "/records"),
            ("publisher", "publisher-.example", "/records"),
            ("publisher", "publisher.example", "/records/../private"),
            ("publisher", "publisher.example", "/records//private"),
            ("publisher", "publisher.example", "/records/"),
            ("publisher", "publisher.example", "/records?x=1"),
        ):
            with self.subTest(args=args):
                with self.assertRaises(ProvenanceError):
                    validate_authority(*args)

    def test_root_authority_has_a_canonical_root_match(self):
        validate_authority("publisher", "publisher.example", "/")
        self.assertTrue(url_matches_authority(
            "https://publisher.example/", "publisher.example", "/"
        ))
        self.assertTrue(url_matches_authority(
            "https://publisher.example/records/mission-001", "publisher.example", "/"
        ))
        self.assertFalse(url_matches_authority(
            "https://publisher.example/records//mission-001", "publisher.example", "/"
        ))

    def test_evidence_root_changes_when_any_bound_field_changes(self):
        record = dict(
            evidence_id="evidence-001",
            authority_id="publisher-a",
            url="https://publisher-a.example/records/mission-001",
            record_hash="ab" * 32,
            subject="mission-001",
            expires_at=3_000_000_100,
        )
        original = evidence_root([record])
        self.assertEqual(len(original), 64)
        self.assertNotEqual(original, evidence_root([{**record, "url": record["url"] + "/v2"}]))
        self.assertNotEqual(original, evidence_root([{**record, "record_hash": "cd" * 32}]))


if __name__ == "__main__":
    unittest.main()
