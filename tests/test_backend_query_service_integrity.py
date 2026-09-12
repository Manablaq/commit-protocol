from __future__ import annotations

from copy import deepcopy
import importlib
import importlib.util
from pathlib import Path
import unittest

from backend.persistence import (
    apply_index_observation,
    apply_transaction_observation,
    empty_persistence_state,
)


def _fixture_module():
    file_name = Path(
        "tests/test_backend_query_service_contract.py"
    )

    spec = importlib.util.spec_from_file_location(
        "commit_query_integrity_fixture",
        file_name,
    )

    if (
        spec is None
        or spec.loader is None
    ):
        raise RuntimeError(
            "unable to load query fixture"
        )

    module = importlib.util.module_from_spec(
        spec
    )

    spec.loader.exec_module(
        module
    )

    return module


FIXTURE = _fixture_module()

CHAIN_ID = FIXTURE.CHAIN_ID
CONTRACT_ADDRESS = (
    FIXTURE.CONTRACT_ADDRESS
)
TX_ID = FIXTURE.TX_ID


def _found_index_view():
    api = importlib.import_module(
        "backend.query_service"
    )

    state = (
        apply_index_observation(
            state=(
                empty_persistence_state()
            ),
            observation=(
                FIXTURE._index_observation(
                    block_number=44,
                    state_status="finalized",
                )
            ),
        )
    )

    return api.build_index_query_view(
        state=state,
        chain_id=CHAIN_ID,
        contract_address=(
            CONTRACT_ADDRESS
        ),
        state_basis="FINALIZED",
    )


def _missing_index_view():
    api = importlib.import_module(
        "backend.query_service"
    )

    return api.build_index_query_view(
        state=(
            empty_persistence_state()
        ),
        chain_id=CHAIN_ID,
        contract_address=(
            CONTRACT_ADDRESS
        ),
        state_basis="FINALIZED",
    )


def _found_transaction_view():
    api = importlib.import_module(
        "backend.query_service"
    )

    state = (
        apply_transaction_observation(
            state=(
                empty_persistence_state()
            ),
            observation=(
                FIXTURE._transaction_observation()
            ),
        )
    )

    return (
        api.build_transaction_query_view(
            state=state,
            genlayer_tx_id=TX_ID,
        )
    )


def _missing_transaction_view():
    api = importlib.import_module(
        "backend.query_service"
    )

    return (
        api.build_transaction_query_view(
            state=(
                empty_persistence_state()
            ),
            genlayer_tx_id=TX_ID,
        )
    )


class BackendQueryServiceIntegrityTests(
    unittest.TestCase
):
    @staticmethod
    def _api():
        return importlib.import_module(
            "backend.query_service"
        )

    def test_public_integrity_validators_are_explicit(
        self,
    ):
        api = self._api()

        self.assertTrue(
            callable(
                getattr(
                    api,
                    "validate_index_query_view",
                    None,
                )
            ),
            "missing index query validator",
        )

        self.assertTrue(
            callable(
                getattr(
                    api,
                    "validate_transaction_query_view",
                    None,
                )
            ),
            "missing transaction query validator",
        )

    def test_generated_found_index_view_validates(
        self,
    ):
        api = self._api()

        validator = (
            api.validate_index_query_view
        )

        view = _found_index_view()

        self.assertIs(
            validator(
                view
            ),
            view,
        )

    def test_generated_missing_index_view_validates(
        self,
    ):
        api = self._api()

        validator = (
            api.validate_index_query_view
        )

        view = _missing_index_view()

        self.assertIs(
            validator(
                view
            ),
            view,
        )

    def test_index_validator_rejects_unknown_fields(
        self,
    ):
        api = self._api()

        validator = (
            api.validate_index_query_view
        )

        forged = {
            **_found_index_view(),
            "latest": True,
        }

        with self.assertRaises(
            api.QueryServiceError
        ):
            validator(
                forged
            )

    def test_index_validator_rejects_basis_forgery(
        self,
    ):
        api = self._api()

        validator = (
            api.validate_index_query_view
        )

        forged = deepcopy(
            _found_index_view()
        )

        forged[
            "state_basis"
        ] = "PROVISIONAL"

        with self.assertRaises(
            api.QueryServiceError
        ):
            validator(
                forged
            )

    def test_index_validator_rejects_source_identity_substitution(
        self,
    ):
        api = self._api()

        validator = (
            api.validate_index_query_view
        )

        forged = deepcopy(
            _found_index_view()
        )

        forged[
            "contract_address"
        ] = (
            "0x"
            + "99" * 20
        )

        with self.assertRaises(
            api.QueryServiceError
        ):
            validator(
                forged
            )

    def test_index_validator_rejects_network_identity_claim_forgery(
        self,
    ):
        api = self._api()

        validator = (
            api.validate_index_query_view
        )

        forged = deepcopy(
            _found_index_view()
        )

        forged[
            "network_identity_verified"
        ] = False

        forged[
            "network_identity_basis"
        ] = "UNVERIFIED_NO_MISSIONS"

        with self.assertRaises(
            api.QueryServiceError
        ):
            validator(
                forged
            )

    def test_index_validator_rejects_not_found_payload_injection(
        self,
    ):
        api = self._api()

        validator = (
            api.validate_index_query_view
        )

        forged = deepcopy(
            _missing_index_view()
        )

        forged[
            "source_record_key"
        ] = (
            "1:"
            + CONTRACT_ADDRESS.lower()
            + ":44"
        )

        forged[
            "source_payload_digest"
        ] = (
            "a"
            * 64
        )

        forged[
            "block_number"
        ] = 44

        with self.assertRaises(
            api.QueryServiceError
        ):
            validator(
                forged
            )

    def test_generated_found_transaction_view_validates(
        self,
    ):
        api = self._api()

        validator = (
            api.validate_transaction_query_view
        )

        view = (
            _found_transaction_view()
        )

        self.assertIs(
            validator(
                view
            ),
            view,
        )

    def test_generated_missing_transaction_view_validates(
        self,
    ):
        api = self._api()

        validator = (
            api.validate_transaction_query_view
        )

        view = (
            _missing_transaction_view()
        )

        self.assertIs(
            validator(
                view
            ),
            view,
        )

    def test_transaction_validator_rejects_unknown_fields(
        self,
    ):
        api = self._api()

        validator = (
            api.validate_transaction_query_view
        )

        forged = {
            **_found_transaction_view(),
            "outer_evm_hash": (
                "0x"
                + "cd" * 32
            ),
        }

        with self.assertRaises(
            api.QueryServiceError
        ):
            validator(
                forged
            )

    def test_transaction_validator_rejects_derived_or_decision_forgery(
        self,
    ):
        api = self._api()

        validator = (
            api.validate_transaction_query_view
        )

        for field, value in (
            (
                "successful",
                False,
            ),
            (
                "finalized",
                False,
            ),
            (
                "final_success",
                False,
            ),
            (
                "application_decision",
                "COMMIT",
            ),
        ):
            forged = deepcopy(
                _found_transaction_view()
            )

            forged[
                field
            ] = value

            with self.subTest(
                field=field
            ):
                with self.assertRaises(
                    api.QueryServiceError
                ):
                    validator(
                        forged
                    )


if __name__ == "__main__":
    unittest.main()
