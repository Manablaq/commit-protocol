from __future__ import annotations

from copy import deepcopy
import importlib
import importlib.util
import json
from pathlib import Path
import unittest

from backend.network_adapter import (
    build_network_index_observation,
)


def _fixture_module():
    file_name = Path(
        "tests/test_backend_network_adapter_contract.py"
    )

    spec = importlib.util.spec_from_file_location(
        "commit_persistence_integrity_fixture",
        file_name,
    )

    if (
        spec is None
        or spec.loader is None
    ):
        raise RuntimeError(
            "unable to load network fixture"
        )

    module = importlib.util.module_from_spec(
        spec
    )

    spec.loader.exec_module(
        module
    )

    return module


FIXTURE = _fixture_module()
FakePinnedReader = FIXTURE.FakePinnedReader


def _observation_with_extension(
    value,
):
    reader = FakePinnedReader()

    reader.source.protocol[
        "extension"
    ] = value

    return build_network_index_observation(
        reader=reader,
        chain_id=1,
        contract_address=(
            "0x"
            + "77" * 20
        ),
        block_number=12345,
        state_status="finalized",
    )


def _canonical_bytes(
    value,
) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(
            ",",
            ":",
        ),
        ensure_ascii=False,
    ).encode(
        "utf-8"
    )


class BackendPersistenceIntegrityTests(
    unittest.TestCase
):
    @staticmethod
    def _api():
        return importlib.import_module(
            "backend.persistence"
        )

    def test_tuple_payload_cannot_alias_list_digest(
        self,
    ):
        api = self._api()

        list_observation = (
            _observation_with_extension(
                ["x"]
            )
        )

        tuple_observation = (
            _observation_with_extension(
                ("x",)
            )
        )

        self.assertNotEqual(
            list_observation,
            tuple_observation,
        )

        self.assertEqual(
            _canonical_bytes(
                list_observation
            ),
            _canonical_bytes(
                tuple_observation
            ),
        )

        state = (
            api.apply_index_observation(
                state=(
                    api.empty_persistence_state()
                ),
                observation=list_observation,
            )
        )

        with self.assertRaises(
            api.PersistenceError
        ):
            api.apply_index_observation(
                state=state,
                observation=tuple_observation,
            )

    def test_non_string_nested_json_key_is_rejected(
        self,
    ):
        api = self._api()

        observation = (
            _observation_with_extension(
                {
                    1: "x",
                }
            )
        )

        with self.assertRaises(
            api.PersistenceError
        ):
            api.apply_index_observation(
                state=(
                    api.empty_persistence_state()
                ),
                observation=observation,
            )

    def test_non_finite_number_is_rejected(
        self,
    ):
        api = self._api()

        for value in (
            float("nan"),
            float("inf"),
            float("-inf"),
        ):
            with self.subTest(
                value=repr(
                    value
                )
            ):
                observation = (
                    _observation_with_extension(
                        value
                    )
                )

                with self.assertRaises(
                    api.PersistenceError
                ):
                    api.apply_index_observation(
                        state=(
                            api.empty_persistence_state()
                        ),
                        observation=observation,
                    )

    def test_state_validator_rejects_non_json_tuple_payload(
        self,
    ):
        api = self._api()

        observation = (
            _observation_with_extension(
                ["x"]
            )
        )

        state = (
            api.apply_index_observation(
                state=(
                    api.empty_persistence_state()
                ),
                observation=observation,
            )
        )

        forged = deepcopy(
            state
        )

        record = next(
            iter(
                forged[
                    "index_records"
                ].values()
            )
        )

        record[
            "payload"
        ][
            "index"
        ][
            "protocol"
        ][
            "extension"
        ] = (
            "x",
        )

        with self.assertRaises(
            api.PersistenceError
        ):
            api.validate_persistence_state(
                forged
            )


if __name__ == "__main__":
    unittest.main()
