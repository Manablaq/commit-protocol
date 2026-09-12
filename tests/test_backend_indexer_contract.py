from __future__ import annotations

from copy import deepcopy
import importlib
import inspect
from pathlib import Path
import unittest


class FakeCanonicalSource:
    def __init__(self) -> None:
        self.calls: list[tuple[object, ...]] = []

        self.protocol = {
            "protocol": "commit",
            "revision": "0.7.0-reviewable-manifest",
            "mission_count": 1,
        }

        self.missions = [
            {
                "mission_id": "mission-001",
                "principal": "0x" + "11" * 20,
                "state": "COMMITTED",
                "version": 1,
                "objective": "atomic procurement",
                "policy_digest": "aa" * 32,
                "intent_digest": "bb" * 32,
                "effect_root": "cc" * 32,
                "evidence_root": "dd" * 32,
                "policy_rule": "all-evidence-and-effects-v1",
                "budget": 10,
                "funded_value": 10,
                "prepared_value": 7,
                "refund_beneficiary": "0x" + "22" * 20,
                "effect_count": 1,
                "evidence_count": 2,
                "supplier_count": 1,
                "decision": "COMMIT",
                "reason_code": "all_sources_and_effects_eligible",
                "decision_nonce": "ee" * 32,
                "evaluation_evidence_root": "ff" * 32,
                "allocation_applied": True,
                "refund_entitlement": 3,
                "evaluation_count": 1,
                "prepare_deadline": 100,
                "recovery_deadline": 200,
                "created_at": 10,
            }
        ]

        self.effects = {
            "mission-001": [
                {
                    "mission_id": "mission-001",
                    "effect_id": "effect-001",
                    "supplier": "0x" + "33" * 20,
                    "digest": "12" * 32,
                    "dependency_id": "",
                    "beneficiary": "0x" + "44" * 20,
                    "value": 7,
                    "expiry": 200,
                }
            ]
        }

        self.evidence = {
            "mission-001": [
                {
                    "mission_id": "mission-001",
                    "evidence_id": "evidence-001",
                    "authority_id": "authority-a",
                    "authority_version": 1,
                    "issuer_address": "0x" + "55" * 20,
                    "record_id": "record-a",
                    "record_version": 1,
                    "mission_version": 1,
                    "url": "https://publisher-a.example/records/a.json",
                    "record_hash": "13" * 32,
                    "subject": "mission-001",
                    "published_at": 20,
                    "expires_at": 200,
                },
                {
                    "mission_id": "mission-001",
                    "evidence_id": "evidence-002",
                    "authority_id": "authority-b",
                    "authority_version": 1,
                    "issuer_address": "0x" + "66" * 20,
                    "record_id": "record-b",
                    "record_version": 1,
                    "mission_version": 1,
                    "url": "https://publisher-b.example/records/b.json",
                    "record_hash": "14" * 32,
                    "subject": "mission-001",
                    "published_at": 21,
                    "expires_at": 200,
                },
            ]
        }

        self.receipts = {
            "mission-001": {
                "receipt_schema": "commit-mission-receipt-v2",
                "manifest_schema": "commit-mission-manifest-v2",
                "protocol": "commit",
                "revision": "0.7.0-reviewable-manifest",
                "chain_id": 1,
                "coordinator": "0x" + "77" * 20,
                "mission_id": "mission-001",
                "principal": "0x" + "11" * 20,
                "version": 1,
                "objective": "atomic procurement",
                "state": "COMMITTED",
                "decision": "COMMIT",
                "reason_code": "all_sources_and_effects_eligible",
                "decision_nonce": "ee" * 32,
                "policy_rule": "all-evidence-and-effects-v1",
                "policy_digest": "aa" * 32,
                "intent_digest": "bb" * 32,
                "effect_root": "cc" * 32,
                "evidence_root": "dd" * 32,
                "evaluation_evidence_root": "ff" * 32,
                "effect_count": 1,
                "evidence_count": 2,
                "budget": 10,
                "funded_value": 10,
                "prepared_value": 7,
                "refund_beneficiary": "0x" + "22" * 20,
                "refund_entitlement": 3,
                "prepare_deadline": 100,
                "recovery_deadline": 200,
                "evaluation_count": 1,
                "allocation_applied": True,
                "external_withdrawal_recovery": False,
            }
        }

        manifest_evidence = []

        for evidence in self.evidence["mission-001"]:
            item = deepcopy(evidence)
            item["authority"] = {
                "authority_id": evidence["authority_id"],
                "active": True,
                "host": (
                    "publisher-a.example"
                    if evidence["authority_id"] == "authority-a"
                    else "publisher-b.example"
                ),
                "path_prefix": "/records",
                "issuer_address": evidence["issuer_address"],
                "authority_version": 1,
            }
            manifest_evidence.append(item)

        self.manifests = {
            "mission-001": {
                "manifest_schema": "commit-mission-manifest-v2",
                "protocol": "commit",
                "revision": "0.7.0-reviewable-manifest",
                "chain_id": 1,
                "coordinator": "0x" + "77" * 20,
                "mission_id": "mission-001",
                "principal": "0x" + "11" * 20,
                "objective": "atomic procurement",
                "policy_rule": "all-evidence-and-effects-v1",
                "policy_digest": "aa" * 32,
                "intent_digest": "bb" * 32,
                "state": "COMMITTED",
                "decision": "COMMIT",
                "reason_code": "all_sources_and_effects_eligible",
                "prepare_deadline": 100,
                "recovery_deadline": 200,
                "effect_count": 1,
                "evidence_count": 2,
                "effect_root": "cc" * 32,
                "evidence_root": "dd" * 32,
                "evaluation_evidence_root": "ff" * 32,
                "allocation_applied": True,
                "effects": deepcopy(
                    self.effects["mission-001"]
                ),
                "evidence": manifest_evidence,
            }
        }

        self.withdrawals = [
            {
                "withdrawal_id": "0",
                "mission_id": "mission-001",
                "beneficiary": "0x" + "44" * 20,
                "amount": 7,
                "status": "DISPATCHED",
            }
        ]

    def protocol_info(self):
        self.calls.append(("protocol_info",))
        return self.protocol

    def get_mission_by_index(self, index: int):
        self.calls.append(
            ("get_mission_by_index", index)
        )
        return self.missions[index]

    def get_mission_receipt(self, mission_id: str):
        self.calls.append(
            ("get_mission_receipt", mission_id)
        )
        return self.receipts[mission_id]

    def get_mission_manifest(self, mission_id: str):
        self.calls.append(
            ("get_mission_manifest", mission_id)
        )
        return self.manifests[mission_id]

    def get_effect_by_index(
        self,
        mission_id: str,
        index: int,
    ):
        self.calls.append(
            (
                "get_effect_by_index",
                mission_id,
                index,
            )
        )
        return self.effects[mission_id][index]

    def get_evidence_by_index(
        self,
        mission_id: str,
        index: int,
    ):
        self.calls.append(
            (
                "get_evidence_by_index",
                mission_id,
                index,
            )
        )
        return self.evidence[mission_id][index]

    def get_withdrawal_count(self):
        self.calls.append(
            ("get_withdrawal_count",)
        )
        return len(self.withdrawals)

    def get_withdrawal_by_index(
        self,
        index: int,
    ):
        self.calls.append(
            ("get_withdrawal_by_index", index)
        )
        return self.withdrawals[index]


class BackendIndexerContractTests(
    unittest.TestCase
):
    @staticmethod
    def _api():
        return importlib.import_module(
            "backend.indexer"
        )

    @staticmethod
    def _build(api, source):
        return api.build_index_snapshot(
            source=source
        )

    def test_public_surface_is_versioned_and_explicit(
        self,
    ):
        api = self._api()

        self.assertEqual(
            api.INDEX_SCHEMA,
            "commit-backend-index-v1",
        )
        self.assertEqual(
            api.SOURCE_MODE,
            "CANONICAL_PULL_READS",
        )
        self.assertEqual(
            api.FINALITY_STATUS,
            "UNVERIFIED",
        )
        self.assertEqual(
            api.EXECUTION_STATUS,
            "UNVERIFIED",
        )
        self.assertTrue(
            issubclass(
                api.IndexerError,
                ValueError,
            )
        )

        build_signature = inspect.signature(
            api.build_index_snapshot
        )

        self.assertEqual(
            list(
                build_signature.parameters
            ),
            ["source"],
        )

        source_parameter = (
            build_signature.parameters[
                "source"
            ]
        )

        self.assertIs(
            source_parameter.kind,
            inspect.Parameter.KEYWORD_ONLY,
        )
        self.assertIs(
            source_parameter.default,
            inspect.Parameter.empty,
        )

        validate_signature = inspect.signature(
            api.validate_index_snapshot
        )

        self.assertEqual(
            list(
                validate_signature.parameters
            ),
            ["snapshot"],
        )

    def test_snapshot_uses_only_canonical_pull_read_methods(
        self,
    ):
        api = self._api()
        source = FakeCanonicalSource()

        self._build(
            api,
            source,
        )

        self.assertEqual(
            source.calls,
            [
                ("protocol_info",),
                ("get_mission_by_index", 0),
                (
                    "get_mission_receipt",
                    "mission-001",
                ),
                (
                    "get_mission_manifest",
                    "mission-001",
                ),
                (
                    "get_effect_by_index",
                    "mission-001",
                    0,
                ),
                (
                    "get_evidence_by_index",
                    "mission-001",
                    0,
                ),
                (
                    "get_evidence_by_index",
                    "mission-001",
                    1,
                ),
                ("get_withdrawal_count",),
                (
                    "get_withdrawal_by_index",
                    0,
                ),
            ],
        )

    def test_mission_enumeration_uses_protocol_mission_count(
        self,
    ):
        api = self._api()
        source = FakeCanonicalSource()

        source.protocol["mission_count"] = 0

        snapshot = self._build(
            api,
            source,
        )

        self.assertEqual(
            snapshot["missions"],
            [],
        )

        self.assertNotIn(
            (
                "get_mission_by_index",
                0,
            ),
            source.calls,
        )

    def test_withdrawal_enumeration_uses_withdrawal_count(
        self,
    ):
        api = self._api()
        source = FakeCanonicalSource()

        source.withdrawals = []

        snapshot = self._build(
            api,
            source,
        )

        self.assertEqual(
            snapshot["withdrawals"],
            [],
        )

        self.assertIn(
            ("get_withdrawal_count",),
            source.calls,
        )

        self.assertFalse(
            any(
                call[0]
                == "get_withdrawal_by_index"
                for call in source.calls
            )
        )

    def test_snapshot_preserves_canonical_onchain_payloads(
        self,
    ):
        api = self._api()
        source = FakeCanonicalSource()

        snapshot = self._build(
            api,
            source,
        )

        entry = snapshot["missions"][0]

        self.assertEqual(
            entry["mission"],
            source.missions[0],
        )
        self.assertEqual(
            entry["receipt"],
            source.receipts["mission-001"],
        )
        self.assertEqual(
            entry["manifest"],
            source.manifests["mission-001"],
        )
        self.assertEqual(
            entry["effects"],
            source.effects["mission-001"],
        )
        self.assertEqual(
            entry["evidence"],
            source.evidence["mission-001"],
        )
        self.assertEqual(
            snapshot["withdrawals"],
            source.withdrawals,
        )

    def test_mission_receipt_manifest_common_fields_must_match(
        self,
    ):
        api = self._api()

        for owner, field, value in (
            (
                "receipts",
                "decision",
                "ABORT",
            ),
            (
                "manifests",
                "effect_root",
                "99" * 32,
            ),
            (
                "receipts",
                "evaluation_evidence_root",
                "88" * 32,
            ),
        ):
            with self.subTest(
                owner=owner,
                field=field,
            ):
                source = FakeCanonicalSource()

                getattr(
                    source,
                    owner,
                )[
                    "mission-001"
                ][
                    field
                ] = value

                with self.assertRaises(
                    api.IndexerError
                ):
                    self._build(
                        api,
                        source,
                    )

    def test_manifest_effects_must_match_indexed_effects(
        self,
    ):
        api = self._api()
        source = FakeCanonicalSource()

        source.manifests[
            "mission-001"
        ][
            "effects"
        ][
            0
        ][
            "digest"
        ] = "99" * 32

        with self.assertRaises(
            api.IndexerError
        ):
            self._build(
                api,
                source,
            )

    def test_manifest_evidence_must_match_indexed_evidence(
        self,
    ):
        api = self._api()
        source = FakeCanonicalSource()

        source.manifests[
            "mission-001"
        ][
            "evidence"
        ][
            0
        ][
            "record_hash"
        ] = "99" * 32

        with self.assertRaises(
            api.IndexerError
        ):
            self._build(
                api,
                source,
            )

    def test_count_domains_are_strict_nonnegative_ints(
        self,
    ):
        api = self._api()

        mutations = (
            (
                "mission_count_bool",
                lambda source: source.protocol.__setitem__(
                    "mission_count",
                    True,
                ),
            ),
            (
                "mission_count_negative",
                lambda source: source.protocol.__setitem__(
                    "mission_count",
                    -1,
                ),
            ),
            (
                "effect_count_bool",
                lambda source: source.missions[
                    0
                ].__setitem__(
                    "effect_count",
                    True,
                ),
            ),
            (
                "evidence_count_negative",
                lambda source: source.missions[
                    0
                ].__setitem__(
                    "evidence_count",
                    -1,
                ),
            ),
        )

        for label, mutate in mutations:
            with self.subTest(
                label=label
            ):
                source = FakeCanonicalSource()
                mutate(source)

                with self.assertRaises(
                    api.IndexerError
                ):
                    self._build(
                        api,
                        source,
                    )

        class BadWithdrawalCount(
            FakeCanonicalSource
        ):
            def get_withdrawal_count(
                self,
            ):
                self.calls.append(
                    ("get_withdrawal_count",)
                )
                return True

        with self.assertRaises(
            api.IndexerError
        ):
            self._build(
                api,
                BadWithdrawalCount(),
            )

    def test_duplicate_mission_ids_are_rejected(
        self,
    ):
        api = self._api()
        source = FakeCanonicalSource()

        source.protocol[
            "mission_count"
        ] = 2

        source.missions.append(
            deepcopy(
                source.missions[0]
            )
        )

        with self.assertRaises(
            api.IndexerError
        ):
            self._build(
                api,
                source,
            )

    def test_withdrawal_identity_is_index_bound_and_unique(
        self,
    ):
        api = self._api()
        source = FakeCanonicalSource()

        source.withdrawals[
            0
        ][
            "withdrawal_id"
        ] = "9"

        with self.assertRaises(
            api.IndexerError
        ):
            self._build(
                api,
                source,
            )

    def test_snapshot_shape_is_exact_and_validator_rejects_extra_fields(
        self,
    ):
        api = self._api()
        source = FakeCanonicalSource()

        snapshot = self._build(
            api,
            source,
        )

        self.assertEqual(
            set(
                snapshot
            ),
            {
                "schema",
                "source_mode",
                "finality_status",
                "execution_status",
                "protocol",
                "missions",
                "withdrawals",
            },
        )

        self.assertEqual(
            set(
                snapshot[
                    "missions"
                ][
                    0
                ]
            ),
            {
                "mission",
                "receipt",
                "manifest",
                "effects",
                "evidence",
            },
        )

        self.assertEqual(
            api.validate_index_snapshot(
                snapshot
            ),
            snapshot,
        )

        forged = {
            **snapshot,
            "run_id": "forbidden",
        }

        with self.assertRaises(
            api.IndexerError
        ):
            api.validate_index_snapshot(
                forged
            )

    def test_snapshot_is_deeply_detached_from_source_objects(
        self,
    ):
        api = self._api()
        source = FakeCanonicalSource()

        snapshot = self._build(
            api,
            source,
        )

        source.protocol[
            "mission_count"
        ] = 99

        source.missions[
            0
        ][
            "state"
        ] = "MUTATED"

        source.effects[
            "mission-001"
        ][
            0
        ][
            "value"
        ] = 999

        source.evidence[
            "mission-001"
        ][
            0
        ][
            "record_hash"
        ] = "00" * 32

        source.withdrawals[
            0
        ][
            "status"
        ] = "MUTATED"

        self.assertEqual(
            snapshot[
                "protocol"
            ][
                "mission_count"
            ],
            1,
        )

        self.assertEqual(
            snapshot[
                "missions"
            ][
                0
            ][
                "mission"
            ][
                "state"
            ],
            "COMMITTED",
        )

        self.assertEqual(
            snapshot[
                "missions"
            ][
                0
            ][
                "effects"
            ][
                0
            ][
                "value"
            ],
            7,
        )

        self.assertEqual(
            snapshot[
                "withdrawals"
            ][
                0
            ][
                "status"
            ],
            "DISPATCHED",
        )

    def test_snapshot_never_claims_finality_or_execution_success(
        self,
    ):
        api = self._api()
        source = FakeCanonicalSource()

        source.missions[
            0
        ][
            "state"
        ] = "COMMITTED"

        snapshot = self._build(
            api,
            source,
        )

        self.assertEqual(
            snapshot[
                "finality_status"
            ],
            "UNVERIFIED",
        )

        self.assertEqual(
            snapshot[
                "execution_status"
            ],
            "UNVERIFIED",
        )

        self.assertNotEqual(
            snapshot[
                "finality_status"
            ],
            "FINALIZED",
        )

        self.assertNotEqual(
            snapshot[
                "execution_status"
            ],
            "FINISHED_WITH_RETURN",
        )

    def test_reviewer_pipeline_fields_are_not_merged_into_onchain_index(
        self,
    ):
        api = self._api()
        source = FakeCanonicalSource()

        snapshot = self._build(
            api,
            source,
        )

        serialized = repr(
            snapshot
        )

        for forbidden in (
            "run_id",
            "bundle_digest",
            "policy_assessment",
            "review_input_binding",
            "confidence_bps",
            "POLICY_ABSTAIN",
            "DECISION_READY",
        ):
            self.assertNotIn(
                forbidden,
                serialized,
            )

        module_source = Path(
            api.__file__
        ).read_text()

        for forbidden_import in (
            "spec_model.review_runner",
            "spec_model.artifacts",
            "spec_model.audit_log",
            "spec_model.confidence_policy",
            "spec_model.review_input",
        ):
            self.assertNotIn(
                forbidden_import,
                module_source,
            )


if __name__ == "__main__":
    unittest.main()
