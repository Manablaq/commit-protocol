import unittest

from eth_hash.auto import keccak

import spec_model.onchain as onchain
import spec_model.provenance as provenance


class ActiveEvidenceRootParityTests(unittest.TestCase):
    def original_records(self):
        return [
            {
                "evidence_id": "evidence-a",
                "authority_id": "publisher-a",
                "authority_version": 1,
                "issuer_address": "0x" + "11" * 20,
                "record_id": "record-a",
                "record_version": 1,
                "mission_id": "mission-001",
                "mission_version": 1,
                "url": "https://publisher-a.example/records/record-a/v1",
                "record_hash": "aa" * 32,
                "subject": "mission-001",
                "published_at": 2_000_000_000,
                "expires_at": 3_000_000_000,
            },
            {
                "evidence_id": "evidence-b",
                "authority_id": "publisher-b",
                "authority_version": 4,
                "issuer_address": "0x" + "22" * 20,
                "record_id": "record-b",
                "record_version": 3,
                "mission_id": "mission-001",
                "mission_version": 1,
                "url": "https://publisher-b.example/records/record-b/v3",
                "record_hash": "bb" * 32,
                "subject": "mission-001",
                "published_at": 2_000_000_010,
                "expires_at": 3_000_000_010,
            },
        ]

    def test_active_root_without_repairs_equals_sealed_v2_root(self):
        records = self.original_records()

        fn = getattr(
            provenance,
            "active_evidence_root",
        )

        self.assertEqual(
            fn(records, {}),
            provenance.evidence_root(records),
        )

    def test_active_root_replaces_only_repaired_record_with_successor(self):
        records = self.original_records()

        repairs = {
            "evidence-a": {
                "status": "READY",
                "authority_id": "publisher-a",
                "authority_version": 1,
                "issuer_address": "0x" + "11" * 20,
                "record_id": "record-a",
                "record_version": 2,
                "url": "https://publisher-a.example/records/record-a/v2",
                "record_hash": "cc" * 32,
                "published_at": 2_000_000_100,
                "expires_at": 3_000_000_100,
            }
        }

        expected_records = [
            {
                **records[0],
                "authority_id": repairs["evidence-a"]["authority_id"],
                "authority_version": repairs["evidence-a"][
                    "authority_version"
                ],
                "issuer_address": repairs["evidence-a"]["issuer_address"],
                "record_id": repairs["evidence-a"]["record_id"],
                "record_version": repairs["evidence-a"]["record_version"],
                "url": repairs["evidence-a"]["url"],
                "record_hash": repairs["evidence-a"]["record_hash"],
                "published_at": repairs["evidence-a"]["published_at"],
                "expires_at": repairs["evidence-a"]["expires_at"],
            },
            records[1],
        ]

        fn = getattr(
            provenance,
            "active_evidence_root",
        )

        active_root = fn(
            records,
            repairs,
        )

        self.assertEqual(
            active_root,
            provenance.evidence_root(
                expected_records
            ),
        )

        self.assertNotEqual(
            active_root,
            provenance.evidence_root(records),
        )


class DecisionV3ParityTests(unittest.TestCase):
    def test_decision_v3_nonce_matches_exact_contract_envelope(self):
        mission_id = "mission-001"
        mission_version = 7
        decision = "COMMIT"
        reason_code = "all_constraints_satisfied"
        effect_root = "11" * 32
        sealed_evidence_root = "22" * 32
        active_evidence_root = "33" * 32

        fields = (
            mission_id,
            str(mission_version),
            decision,
            reason_code,
            effect_root,
            sealed_evidence_root,
            active_evidence_root,
        )

        payload = (
            "commit-decision-v3"
            + "".join(
                onchain.frame(value)
                for value in fields
            )
        )

        expected = keccak(
            payload.encode("utf-8")
        ).hex()

        fn = getattr(
            onchain,
            "decision_nonce_v3",
        )

        self.assertEqual(
            fn(
                mission_id=mission_id,
                mission_version=mission_version,
                decision=decision,
                reason_code=reason_code,
                effect_root=effect_root,
                sealed_evidence_root=sealed_evidence_root,
                active_evidence_root=active_evidence_root,
            ),
            expected,
        )

    def test_decision_v3_nonce_binds_active_evidence_root(self):
        fn = getattr(
            onchain,
            "decision_nonce_v3",
        )

        base = dict(
            mission_id="mission-001",
            mission_version=7,
            decision="COMMIT",
            reason_code="all_constraints_satisfied",
            effect_root="11" * 32,
            sealed_evidence_root="22" * 32,
            active_evidence_root="33" * 32,
        )

        original = fn(**base)

        changed = fn(
            **{
                **base,
                "active_evidence_root": "44" * 32,
            }
        )

        self.assertNotEqual(
            original,
            changed,
        )


if __name__ == "__main__":
    unittest.main()
