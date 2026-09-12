from __future__ import annotations

from copy import deepcopy
import importlib.util
from pathlib import Path
import unittest

from backend.indexer import (
    IndexerError,
    build_index_snapshot,
    validate_index_snapshot,
)


def _load_fixture_source_type():
    test_path = Path(
        "tests/test_backend_indexer_contract.py"
    )

    spec = importlib.util.spec_from_file_location(
        "commit_backend_indexer_contract_fixture",
        test_path,
    )

    if (
        spec is None
        or spec.loader is None
    ):
        raise RuntimeError(
            "unable to load frozen indexer contract fixture"
        )

    module = importlib.util.module_from_spec(
        spec
    )

    spec.loader.exec_module(
        module
    )

    return module.FakeCanonicalSource


FakeCanonicalSource = (
    _load_fixture_source_type()
)


class BackendIndexerIntegrityTests(
    unittest.TestCase
):
    def test_effect_child_must_match_parent_mission(
        self,
    ):
        source = FakeCanonicalSource()

        source.effects[
            "mission-001"
        ][
            0
        ][
            "mission_id"
        ] = "mission-999"

        source.manifests[
            "mission-001"
        ][
            "effects"
        ][
            0
        ][
            "mission_id"
        ] = "mission-999"

        with self.assertRaises(
            IndexerError
        ):
            build_index_snapshot(
                source=source
            )

    def test_evidence_child_must_match_parent_mission(
        self,
    ):
        source = FakeCanonicalSource()

        source.evidence[
            "mission-001"
        ][
            0
        ][
            "mission_id"
        ] = "mission-999"

        source.manifests[
            "mission-001"
        ][
            "evidence"
        ][
            0
        ][
            "mission_id"
        ] = "mission-999"

        with self.assertRaises(
            IndexerError
        ):
            build_index_snapshot(
                source=source
            )

    def test_duplicate_effect_ids_are_rejected(
        self,
    ):
        source = FakeCanonicalSource()

        duplicate = deepcopy(
            source.effects[
                "mission-001"
            ][
                0
            ]
        )

        source.effects[
            "mission-001"
        ].append(
            duplicate
        )

        source.manifests[
            "mission-001"
        ][
            "effects"
        ].append(
            deepcopy(
                duplicate
            )
        )

        source.missions[
            0
        ][
            "effect_count"
        ] = 2

        source.receipts[
            "mission-001"
        ][
            "effect_count"
        ] = 2

        source.manifests[
            "mission-001"
        ][
            "effect_count"
        ] = 2

        with self.assertRaises(
            IndexerError
        ):
            build_index_snapshot(
                source=source
            )

    def test_duplicate_evidence_ids_are_rejected(
        self,
    ):
        source = FakeCanonicalSource()

        duplicate = deepcopy(
            source.evidence[
                "mission-001"
            ][
                0
            ]
        )

        source.evidence[
            "mission-001"
        ].append(
            duplicate
        )

        source.manifests[
            "mission-001"
        ][
            "evidence"
        ].append(
            deepcopy(
                source.manifests[
                    "mission-001"
                ][
                    "evidence"
                ][
                    0
                ]
            )
        )

        source.missions[
            0
        ][
            "evidence_count"
        ] = 3

        source.receipts[
            "mission-001"
        ][
            "evidence_count"
        ] = 3

        source.manifests[
            "mission-001"
        ][
            "evidence_count"
        ] = 3

        with self.assertRaises(
            IndexerError
        ):
            build_index_snapshot(
                source=source
            )

    def test_withdrawal_must_reference_indexed_mission(
        self,
    ):
        source = FakeCanonicalSource()

        source.withdrawals[
            0
        ][
            "mission_id"
        ] = "mission-999"

        with self.assertRaises(
            IndexerError
        ):
            build_index_snapshot(
                source=source
            )

    def test_effect_records_must_be_objects(
        self,
    ):
        source = FakeCanonicalSource()

        source.effects[
            "mission-001"
        ][
            0
        ] = "forged-effect"

        source.manifests[
            "mission-001"
        ][
            "effects"
        ][
            0
        ] = "forged-effect"

        with self.assertRaises(
            IndexerError
        ):
            build_index_snapshot(
                source=source
            )

    def test_validator_rejects_cross_mission_effect_substitution(
        self,
    ):
        source = FakeCanonicalSource()

        snapshot = build_index_snapshot(
            source=source
        )

        forged = deepcopy(
            snapshot
        )

        forged[
            "missions"
        ][
            0
        ][
            "effects"
        ][
            0
        ][
            "mission_id"
        ] = "mission-999"

        forged[
            "missions"
        ][
            0
        ][
            "manifest"
        ][
            "effects"
        ][
            0
        ][
            "mission_id"
        ] = "mission-999"

        with self.assertRaises(
            IndexerError
        ):
            validate_index_snapshot(
                forged
            )

    def test_source_read_failures_are_normalized(
        self,
    ):
        class BrokenCanonicalSource(
            FakeCanonicalSource
        ):
            def get_mission_by_index(
                self,
                index: int,
            ):
                raise RuntimeError(
                    "source boom"
                )

        with self.assertRaises(
            IndexerError
        ):
            build_index_snapshot(
                source=BrokenCanonicalSource()
            )


if __name__ == "__main__":
    unittest.main()
