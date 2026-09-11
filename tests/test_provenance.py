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
            authority_version=7,
            issuer_address="0x" + "11" * 20,
            record_id="record-001",
            record_version=3,
            mission_id="mission-001",
            mission_version=2,
            url="https://publisher-a.example/records/mission-001",
            record_hash="ab" * 32,
            subject="mission-001",
            published_at=2_000_000_000,
            expires_at=3_000_000_100,
        )

        original = evidence_root([record])

        self.assertEqual(len(original), 64)

        mutations = {
            "evidence_id": "evidence-002",
            "authority_id": "publisher-b",
            "authority_version": 8,
            "issuer_address": "0x" + "22" * 20,
            "record_id": "record-002",
            "record_version": 4,
            "mission_id": "mission-002",
            "mission_version": 3,
            "url": record["url"] + "/v2",
            "record_hash": "cd" * 32,
            "subject": "mission-002",
            "published_at": 2_000_000_001,
            "expires_at": 3_000_000_101,
        }

        for field, replacement in mutations.items():
            with self.subTest(field=field):
                changed = {
                    **record,
                    field: replacement,
                }
                self.assertNotEqual(
                    original,
                    evidence_root([changed]),
                )



if __name__ == "__main__":
    unittest.main()

class EvidenceCommitmentV2Tests(unittest.TestCase):
    def _record(self):
        return {
            "evidence_id": "evidence-001",
            "authority_id": "publisher-a",
            "authority_version": 7,
            "issuer_address": "0x" + "11" * 20,
            "record_id": "record-001",
            "record_version": 3,
            "mission_id": "mission-001",
            "mission_version": 2,
            "url": "https://publisher-a.example/records/record-001",
            "record_hash": "ab" * 32,
            "subject": "mission-001",
            "published_at": 2_000_000_000,
            "expires_at": 3_000_000_100,
        }

    def test_evidence_root_matches_exact_v2_commitment(self):
        from eth_hash.auto import keccak
        from spec_model.onchain import frame

        record = self._record()

        fields = (
            record["evidence_id"],
            record["authority_id"],
            str(record["authority_version"]),
            record["issuer_address"],
            record["record_id"],
            str(record["record_version"]),
            record["mission_id"],
            str(record["mission_version"]),
            record["url"],
            record["record_hash"],
            record["subject"],
            str(record["published_at"]),
            str(record["expires_at"]),
        )

        leaf_payload = (
            "commit-evidence-leaf-v2"
            + "".join(frame(str(value)) for value in fields)
        )
        leaf = keccak(
            leaf_payload.encode("utf-8")
        ).hex()

        root_payload = (
            "commit-evidence-root-v2"
            + frame("1")
            + frame(leaf)
        )
        expected = keccak(
            root_payload.encode("utf-8")
        ).hex()

        self.assertEqual(
            evidence_root([record]),
            expected,
        )

    def test_evidence_root_binds_every_v2_security_field(self):
        record = self._record()
        original = evidence_root([record])

        mutations = {
            "authority_version": 8,
            "issuer_address": "0x" + "22" * 20,
            "record_id": "record-002",
            "record_version": 4,
            "mission_id": "mission-002",
            "mission_version": 3,
            "published_at": 2_000_000_001,
        }

        for field, replacement in mutations.items():
            with self.subTest(field=field):
                changed = {
                    **record,
                    field: replacement,
                }
                self.assertNotEqual(
                    original,
                    evidence_root([changed]),
                )
