from __future__ import annotations

from copy import deepcopy
import importlib
import importlib.util
from pathlib import Path
import unittest


def _network_fixture_module():
    file_name = Path(
        "tests/test_backend_network_adapter_contract.py"
    )

    spec = importlib.util.spec_from_file_location(
        "commit_network_integrity_fixture",
        file_name,
    )

    if (
        spec is None
        or spec.loader is None
    ):
        raise RuntimeError(
            "unable to load network adapter fixture"
        )

    module = importlib.util.module_from_spec(
        spec
    )

    spec.loader.exec_module(
        module
    )

    return module


FIXTURE = _network_fixture_module()
FakePinnedReader = FIXTURE.FakePinnedReader


class BackendNetworkAdapterIntegrityTests(
    unittest.TestCase
):
    @staticmethod
    def _api():
        return importlib.import_module(
            "backend.network_adapter"
        )

    @staticmethod
    def _observation(
        api,
        *,
        reader=None,
        contract_address=None,
        state_status="finalized",
    ):
        if reader is None:
            reader = FakePinnedReader()

        if contract_address is None:
            contract_address = (
                "0x"
                + "77" * 20
            )

        return (
            api.build_network_index_observation(
                reader=reader,
                chain_id=1,
                contract_address=contract_address,
                block_number=12345,
                state_status=state_status,
            )
        )

    @staticmethod
    def _transaction(
        api,
    ):
        return (
            api.classify_transaction_observation(
                genlayer_tx_id=(
                    "0x"
                    + "ab" * 32
                ),
                status_code=7,
                status_name="Finalized",
                execution_result=(
                    "FINISHED_WITH_RETURN"
                ),
            )
        )

    def test_public_integrity_validators_are_explicit(
        self,
    ):
        api = self._api()

        self.assertTrue(
            callable(
                getattr(
                    api,
                    "validate_network_index_observation",
                    None,
                )
            ),
            "missing network observation validator",
        )

        self.assertTrue(
            callable(
                getattr(
                    api,
                    "validate_transaction_observation",
                    None,
                )
            ),
            "missing transaction observation validator",
        )

    def test_mission_bearing_observation_marks_identity_verified(
        self,
    ):
        api = self._api()

        observation = self._observation(
            api
        )

        self.assertIn(
            "network_identity_verified",
            observation,
            "missing network identity verification field",
        )

        self.assertIn(
            "network_identity_basis",
            observation,
            "missing network identity basis field",
        )

        self.assertIs(
            observation[
                "network_identity_verified"
            ],
            True,
        )

        self.assertEqual(
            observation[
                "network_identity_basis"
            ],
            "MISSION_RECEIPT_MANIFEST",
        )

    def test_empty_mission_domain_marks_identity_unverified(
        self,
    ):
        api = self._api()
        reader = FakePinnedReader()

        reader.source.protocol[
            "mission_count"
        ] = 0

        observation = self._observation(
            api,
            reader=reader,
        )

        self.assertIn(
            "network_identity_verified",
            observation,
            "missing network identity verification field",
        )

        self.assertIn(
            "network_identity_basis",
            observation,
            "missing network identity basis field",
        )

        self.assertIs(
            observation[
                "network_identity_verified"
            ],
            False,
        )

        self.assertEqual(
            observation[
                "network_identity_basis"
            ],
            "UNVERIFIED_NO_MISSIONS",
        )

    def test_zero_contract_address_is_rejected_even_without_missions(
        self,
    ):
        api = self._api()
        reader = FakePinnedReader()

        reader.source.protocol[
            "mission_count"
        ] = 0

        with self.assertRaises(
            api.NetworkAdapterError
        ):
            self._observation(
                api,
                reader=reader,
                contract_address=(
                    "0x"
                    + "00" * 20
                ),
            )

    def test_network_validator_rejects_state_basis_forgery(
        self,
    ):
        api = self._api()

        observation = self._observation(
            api,
            state_status="accepted",
        )

        forged = deepcopy(
            observation
        )

        forged[
            "state_basis"
        ] = "FINALIZED"

        validator = (
            api.validate_network_index_observation
        )

        with self.assertRaises(
            api.NetworkAdapterError
        ):
            validator(
                forged
            )

    def test_network_validator_rejects_read_mode_forgery(
        self,
    ):
        api = self._api()

        forged = deepcopy(
            self._observation(
                api
            )
        )

        forged[
            "read_mode"
        ] = "LATEST_ACCEPTED"

        validator = (
            api.validate_network_index_observation
        )

        with self.assertRaises(
            api.NetworkAdapterError
        ):
            validator(
                forged
            )

    def test_network_validator_rejects_index_finality_promotion(
        self,
    ):
        api = self._api()

        forged = deepcopy(
            self._observation(
                api
            )
        )

        forged[
            "index"
        ][
            "finality_status"
        ] = "FINALIZED"

        validator = (
            api.validate_network_index_observation
        )

        with self.assertRaises(
            api.NetworkAdapterError
        ):
            validator(
                forged
            )

    def test_network_validator_rejects_identity_substitution(
        self,
    ):
        api = self._api()

        forged = deepcopy(
            self._observation(
                api
            )
        )

        forged[
            "contract_address"
        ] = (
            "0x"
            + "99" * 20
        )

        validator = (
            api.validate_network_index_observation
        )

        with self.assertRaises(
            api.NetworkAdapterError
        ):
            validator(
                forged
            )

    def test_network_validator_rejects_unknown_fields(
        self,
    ):
        api = self._api()

        forged = {
            **self._observation(
                api
            ),
            "outer_evm_hash": (
                "0x"
                + "cd" * 32
            ),
        }

        validator = (
            api.validate_network_index_observation
        )

        with self.assertRaises(
            api.NetworkAdapterError
        ):
            validator(
                forged
            )

    def test_transaction_validator_rejects_derived_boolean_forgery(
        self,
    ):
        api = self._api()

        forged = {
            **self._transaction(
                api
            ),
            "final_success": False,
        }

        validator = (
            api.validate_transaction_observation
        )

        with self.assertRaises(
            api.NetworkAdapterError
        ):
            validator(
                forged
            )

    def test_transaction_validator_rejects_application_decision_injection(
        self,
    ):
        api = self._api()

        forged = {
            **self._transaction(
                api
            ),
            "application_decision": "COMMIT",
        }

        validator = (
            api.validate_transaction_observation
        )

        with self.assertRaises(
            api.NetworkAdapterError
        ):
            validator(
                forged
            )

    def test_transaction_validator_rejects_unknown_fields(
        self,
    ):
        api = self._api()

        forged = {
            **self._transaction(
                api
            ),
            "outer_evm_hash": (
                "0x"
                + "cd" * 32
            ),
        }

        validator = (
            api.validate_transaction_observation
        )

        with self.assertRaises(
            api.NetworkAdapterError
        ):
            validator(
                forged
            )


if __name__ == "__main__":
    unittest.main()
