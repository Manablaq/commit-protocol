from __future__ import annotations

from copy import deepcopy
import importlib
import importlib.util
from pathlib import Path
from unittest.mock import patch
from urllib.parse import urlencode
import unittest


def _contract_fixture():
    file_name = Path(
        "tests/test_backend_service_api_contract.py"
    )

    spec = importlib.util.spec_from_file_location(
        "commit_service_integrity_fixture",
        file_name,
    )

    if (
        spec is None
        or spec.loader is None
    ):
        raise RuntimeError(
            "unable to load service contract fixture"
        )

    module = importlib.util.module_from_spec(
        spec
    )

    spec.loader.exec_module(
        module
    )

    return module


FIXTURE = _contract_fixture()


def _api():
    return importlib.import_module(
        "backend.service_api"
    )


def _valid_index_query() -> str:
    return urlencode(
        {
            "chain_id": (
                FIXTURE.CHAIN_ID
            ),
            "contract_address": (
                FIXTURE.CONTRACT_ADDRESS
            ),
            "state_basis": (
                "FINALIZED"
            ),
        }
    )


class BackendServiceApiIntegrityTests(
    unittest.TestCase
):
    def test_unknown_index_query_parameter_is_rejected_before_storage_read(
        self,
    ):
        api = _api()

        store = FIXTURE.FakeStore(
            FIXTURE._index_snapshot()
        )

        app = api.create_app(
            store=store
        )

        query = urlencode(
            {
                "chain_id": (
                    FIXTURE.CHAIN_ID
                ),
                "contract_address": (
                    FIXTURE.CONTRACT_ADDRESS
                ),
                "state_basis": (
                    "FINALIZED"
                ),
                "unexpected": (
                    "value"
                ),
            }
        )

        status, _body = (
            FIXTURE._request(
                app,
                path="/api/v1/index",
                query=query,
            )
        )

        self.assertEqual(
            status,
            422,
            "unknown query parameter was accepted",
        )

        self.assertEqual(
            store.loads,
            0,
            "unknown query parameter reached storage",
        )

    def test_matching_vercel_route_capture_is_not_public_query_input(
        self,
    ):
        api = _api()

        store = FIXTURE.FakeStore(
            FIXTURE._index_snapshot()
        )

        app = api.create_app(
            store=store
        )

        query = urlencode(
            [
                (
                    "chain_id",
                    str(
                        FIXTURE.CHAIN_ID
                    ),
                ),
                (
                    "contract_address",
                    FIXTURE.CONTRACT_ADDRESS,
                ),
                (
                    "state_basis",
                    "FINALIZED",
                ),
                (
                    "1",
                    "index",
                ),
            ]
        )

        status, body = FIXTURE._request(
            app,
            path="/api/v1/index",
            query=query,
        )

        self.assertEqual(
            status,
            200,
        )
        self.assertIs(
            body[
                "found"
            ],
            True,
        )
        self.assertEqual(
            store.loads,
            1,
        )

    def test_matching_vercel_transaction_capture_is_not_public_query_input(
        self,
    ):
        api = _api()

        store = FIXTURE.FakeStore(
            FIXTURE._transaction_snapshot()
        )

        app = api.create_app(
            store=store
        )

        suffix = (
            "transactions/"
            + FIXTURE.TX_ID
        )

        status, body = FIXTURE._request(
            app,
            path=(
                "/api/v1/"
                + suffix
            ),
            query=urlencode(
                {
                    "1": suffix,
                }
            ),
        )

        self.assertEqual(
            status,
            200,
        )
        self.assertIs(
            body[
                "found"
            ],
            True,
        )
        self.assertEqual(
            store.loads,
            1,
        )

    def test_reserved_vercel_capture_value_is_ignored_before_public_shape_validation(
        self,
    ):
        api = _api()

        store = FIXTURE.FakeStore(
            FIXTURE._index_snapshot()
        )

        app = api.create_app(
            store=store
        )

        query = urlencode(
            [
                (
                    "chain_id",
                    str(
                        FIXTURE.CHAIN_ID
                    ),
                ),
                (
                    "contract_address",
                    FIXTURE.CONTRACT_ADDRESS,
                ),
                (
                    "state_basis",
                    "FINALIZED",
                ),
                (
                    "1",
                    "wrong-route",
                ),
            ]
        )

        status, body = FIXTURE._request(
            app,
            path="/api/v1/index",
            query=query,
        )

        self.assertEqual(
            status,
            200,
        )
        self.assertIs(
            body["found"],
            True,
        )
        self.assertEqual(
            store.loads,
            1,
        )

    def test_duplicate_index_state_basis_is_rejected_before_storage_read(
        self,
    ):
        api = _api()

        store = FIXTURE.FakeStore(
            FIXTURE._index_snapshot()
        )

        app = api.create_app(
            store=store
        )

        query = urlencode(
            [
                (
                    "chain_id",
                    str(
                        FIXTURE.CHAIN_ID
                    ),
                ),
                (
                    "contract_address",
                    (
                        FIXTURE.CONTRACT_ADDRESS
                    ),
                ),
                (
                    "state_basis",
                    "FINALIZED",
                ),
                (
                    "state_basis",
                    "FINALIZED",
                ),
            ]
        )

        status, _body = (
            FIXTURE._request(
                app,
                path="/api/v1/index",
                query=query,
            )
        )

        self.assertEqual(
            status,
            422,
            "duplicate state_basis was accepted",
        )

        self.assertEqual(
            store.loads,
            0,
            "duplicate state_basis reached storage",
        )

    def test_invalid_state_basis_is_rejected_before_storage_read(
        self,
    ):
        api = _api()

        store = FIXTURE.FakeStore(
            FIXTURE._index_snapshot()
        )

        app = api.create_app(
            store=store
        )

        query = urlencode(
            {
                "chain_id": (
                    FIXTURE.CHAIN_ID
                ),
                "contract_address": (
                    FIXTURE.CONTRACT_ADDRESS
                ),
                "state_basis": (
                    "INVALID"
                ),
            }
        )

        status, _body = (
            FIXTURE._request(
                app,
                path="/api/v1/index",
                query=query,
            )
        )

        self.assertEqual(
            status,
            422,
        )

        self.assertEqual(
            store.loads,
            0,
            "invalid state basis reached storage",
        )

    def test_invalid_contract_address_is_rejected_before_storage_read(
        self,
    ):
        api = _api()

        store = FIXTURE.FakeStore(
            FIXTURE._index_snapshot()
        )

        app = api.create_app(
            store=store
        )

        query = urlencode(
            {
                "chain_id": (
                    FIXTURE.CHAIN_ID
                ),
                "contract_address": (
                    "not-an-address"
                ),
                "state_basis": (
                    "FINALIZED"
                ),
            }
        )

        status, _body = (
            FIXTURE._request(
                app,
                path="/api/v1/index",
                query=query,
            )
        )

        self.assertEqual(
            status,
            422,
        )

        self.assertEqual(
            store.loads,
            0,
            "invalid contract address reached storage",
        )

    def test_invalid_transaction_id_is_rejected_before_storage_read(
        self,
    ):
        api = _api()

        store = FIXTURE.FakeStore(
            FIXTURE._transaction_snapshot()
        )

        app = api.create_app(
            store=store
        )

        status, _body = (
            FIXTURE._request(
                app,
                path=(
                    "/api/v1/transactions/"
                    "not-a-valid-transaction-id"
                ),
            )
        )

        self.assertEqual(
            status,
            422,
        )

        self.assertEqual(
            store.loads,
            0,
            "invalid transaction id reached storage",
        )

    def test_corrupt_persistence_state_is_backend_unavailable_not_client_error(
        self,
    ):
        api = _api()

        snapshot = deepcopy(
            FIXTURE._index_snapshot()
        )

        snapshot[
            "state"
        ][
            "schema"
        ] = (
            "tampered-persistence-state"
        )

        store = FIXTURE.FakeStore(
            snapshot
        )

        app = api.create_app(
            store=store
        )

        status, body = (
            FIXTURE._request(
                app,
                path="/api/v1/index",
                query=(
                    _valid_index_query()
                ),
            )
        )

        self.assertEqual(
            status,
            503,
            "corrupt persisted state was classified as client error",
        )

        self.assertEqual(
            body,
            {
                "schema": (
                    api.SERVICE_ERROR_SCHEMA
                ),
                "error": (
                    "BACKEND_STATE_UNAVAILABLE"
                ),
            },
        )

        self.assertEqual(
            store.loads,
            1,
        )

        rendered = repr(
            body
        ).lower()

        self.assertNotIn(
            "tampered",
            rendered,
        )

    def test_unexpected_projection_failure_fails_closed_without_leak(
        self,
    ):
        api = _api()

        store = FIXTURE.FakeStore(
            FIXTURE._index_snapshot()
        )

        app = api.create_app(
            store=store
        )

        try:
            with patch(
                "backend.service_api."
                "build_index_query_view",
                side_effect=RuntimeError(
                    "secret projection detail"
                ),
            ):
                status, body = (
                    FIXTURE._request(
                        app,
                        path="/api/v1/index",
                        query=(
                            _valid_index_query()
                        ),
                    )
                )
        except RuntimeError as exc:
            self.fail(
                "projection failure escaped service boundary: "
                + str(
                    exc
                )
            )

        self.assertEqual(
            status,
            503,
            "unexpected projection failure did not fail closed",
        )

        self.assertEqual(
            body,
            {
                "schema": (
                    api.SERVICE_ERROR_SCHEMA
                ),
                "error": (
                    "BACKEND_STATE_UNAVAILABLE"
                ),
            },
        )

        self.assertEqual(
            store.loads,
            1,
        )

        self.assertNotIn(
            "secret",
            repr(
                body
            ).lower(),
        )

    def test_valid_finalized_index_still_reads_exactly_once(
        self,
    ):
        api = _api()

        store = FIXTURE.FakeStore(
            FIXTURE._index_snapshot()
        )

        app = api.create_app(
            store=store
        )

        status, body = (
            FIXTURE._request(
                app,
                path="/api/v1/index",
                query=(
                    _valid_index_query()
                ),
            )
        )

        self.assertEqual(
            status,
            200,
        )

        self.assertIs(
            body[
                "found"
            ],
            True,
        )

        self.assertEqual(
            body[
                "state_basis"
            ],
            "FINALIZED",
        )

        self.assertEqual(
            store.loads,
            1,
        )

    def test_valid_finalized_transaction_still_reads_exactly_once(
        self,
    ):
        api = _api()

        store = FIXTURE.FakeStore(
            FIXTURE._transaction_snapshot()
        )

        app = api.create_app(
            store=store
        )

        status, body = (
            FIXTURE._request(
                app,
                path=(
                    "/api/v1/transactions/"
                    + FIXTURE.TX_ID
                ),
            )
        )

        self.assertEqual(
            status,
            200,
        )

        self.assertIs(
            body[
                "found"
            ],
            True,
        )

        self.assertEqual(
            body[
                "status_name"
            ],
            "Finalized",
        )

        self.assertEqual(
            store.loads,
            1,
        )


if __name__ == "__main__":
    unittest.main()
