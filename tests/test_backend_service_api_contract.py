from __future__ import annotations

import asyncio
from copy import deepcopy
import importlib
import importlib.util
import json
from pathlib import Path
from urllib.parse import urlencode
import unittest

from backend.network_adapter import (
    classify_transaction_observation,
)
from backend.persistence import (
    apply_index_observation,
    apply_transaction_observation,
    empty_persistence_state,
)
from backend.storage_adapter import (
    DurableStateStore,
    StorageCorruptionError,
)


CHAIN_ID = 1

CONTRACT_ADDRESS = (
    "0x"
    + "77" * 20
)

TX_ID = (
    "0x"
    + "ab" * 32
)

NAMESPACE = (
    "commit-backend-state"
)


def _storage_fixture():
    file_name = Path(
        "tests/test_backend_storage_adapter_contract.py"
    )

    spec = importlib.util.spec_from_file_location(
        "commit_service_storage_fixture",
        file_name,
    )

    if (
        spec is None
        or spec.loader is None
    ):
        raise RuntimeError(
            "unable to load storage fixture"
        )

    module = importlib.util.module_from_spec(
        spec
    )

    spec.loader.exec_module(
        module
    )

    return module


def _query_fixture():
    file_name = Path(
        "tests/test_backend_query_service_contract.py"
    )

    spec = importlib.util.spec_from_file_location(
        "commit_service_query_fixture",
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


STORAGE_FIXTURE = _storage_fixture()
QUERY_FIXTURE = _query_fixture()


def _durable_snapshot(
    state,
):
    driver = (
        STORAGE_FIXTURE.FakeAtomicDriver()
    )

    store = DurableStateStore(
        driver=driver,
        namespace=NAMESPACE,
    )

    store.save(
        state=state,
        expected_revision=0,
    )

    return store.load()


def _index_snapshot():
    observation = (
        QUERY_FIXTURE._index_observation(
            block_number=44,
            state_status="finalized",
        )
    )

    state = (
        apply_index_observation(
            state=(
                empty_persistence_state()
            ),
            observation=observation,
        )
    )

    return _durable_snapshot(
        state
    )


def _transaction_snapshot():
    observation = (
        classify_transaction_observation(
            genlayer_tx_id=TX_ID,
            status_code=7,
            status_name="Finalized",
            execution_result=(
                "FINISHED_WITH_RETURN"
            ),
        )
    )

    state = (
        apply_transaction_observation(
            state=(
                empty_persistence_state()
            ),
            observation=observation,
        )
    )

    return _durable_snapshot(
        state
    )


def _empty_snapshot():
    return {
        "schema": (
            "commit-backend-storage-snapshot-v1"
        ),
        "revision": 0,
        "state_digest": (
            STORAGE_FIXTURE._digest(
                empty_persistence_state()
            )
        ),
        "state": (
            empty_persistence_state()
        ),
    }


class FakeStore:
    def __init__(
        self,
        snapshot,
        *,
        error=None,
    ):
        self.snapshot = deepcopy(
            snapshot
        )

        self.error = error

        self.loads = 0

    def load(
        self,
    ):
        self.loads += 1

        if self.error is not None:
            raise self.error

        return deepcopy(
            self.snapshot
        )


async def _request_async(
    app,
    *,
    path: str,
    query: str = "",
):
    messages = []

    request_sent = False

    async def receive():
        nonlocal request_sent

        if not request_sent:
            request_sent = True

            return {
                "type": "http.request",
                "body": b"",
                "more_body": False,
            }

        return {
            "type": "http.disconnect",
        }

    async def send(
        message,
    ):
        messages.append(
            message
        )

    scope = {
        "type": "http",
        "asgi": {
            "version": "3.0",
        },
        "http_version": "1.1",
        "method": "GET",
        "scheme": "https",
        "path": path,
        "raw_path": (
            path.encode(
                "ascii"
            )
        ),
        "query_string": (
            query.encode(
                "ascii"
            )
        ),
        "headers": [],
        "client": (
            "127.0.0.1",
            50000,
        ),
        "server": (
            "commit.example",
            443,
        ),
        "root_path": "",
    }

    await app(
        scope,
        receive,
        send,
    )

    start = next(
        message
        for message in messages
        if (
            message[
                "type"
            ]
            == "http.response.start"
        )
    )

    body = b"".join(
        message.get(
            "body",
            b"",
        )
        for message in messages
        if (
            message[
                "type"
            ]
            == "http.response.body"
        )
    )

    payload = (
        json.loads(
            body.decode(
                "utf-8"
            )
        )
        if body
        else None
    )

    return (
        start[
            "status"
        ],
        payload,
    )


def _request(
    app,
    *,
    path: str,
    query: str = "",
):
    return asyncio.run(
        _request_async(
            app,
            path=path,
            query=query,
        )
    )


class BackendServiceApiContractTests(
    unittest.TestCase
):
    @staticmethod
    def _api():
        return importlib.import_module(
            "backend.service_api"
        )

    def test_public_surface_selects_fastapi_and_versioned_api(
        self,
    ):
        api = self._api()

        self.assertEqual(
            api.SERVICE_SCHEMA,
            "commit-backend-service-v1",
        )

        self.assertEqual(
            api.SERVICE_ERROR_SCHEMA,
            "commit-backend-service-error-v1",
        )

        self.assertEqual(
            api.HTTP_FRAMEWORK,
            "FASTAPI",
        )

        self.assertEqual(
            api.API_PREFIX,
            "/api/v1",
        )

        self.assertTrue(
            callable(
                api.create_app
            )
        )

    def test_public_route_surface_is_exact_and_read_only(
        self,
    ):
        api = self._api()

        app = api.create_app(
            store=FakeStore(
                _empty_snapshot()
            )
        )

        public = {}

        for route in app.routes:
            path = getattr(
                route,
                "path",
                "",
            )

            if not path.startswith(
                "/api/v1"
            ):
                continue

            methods = set(
                getattr(
                    route,
                    "methods",
                    set(),
                )
            )

            public[
                path
            ] = methods

        self.assertEqual(
            set(
                public
            ),
            {
                "/api/v1/health",
                "/api/v1/index",
                "/api/v1/transactions/{genlayer_tx_id}",
            },
        )

        for methods in public.values():
            self.assertEqual(
                methods,
                {
                    "GET",
                },
            )

    def test_health_is_liveness_only_and_does_not_read_storage(
        self,
    ):
        api = self._api()

        store = FakeStore(
            _empty_snapshot()
        )

        app = api.create_app(
            store=store
        )

        status, body = _request(
            app,
            path="/api/v1/health",
        )

        self.assertEqual(
            status,
            200,
        )

        self.assertEqual(
            body,
            {
                "schema": (
                    api.SERVICE_SCHEMA
                ),
                "status": "ok",
            },
        )

        self.assertEqual(
            store.loads,
            0,
        )

    def test_index_query_requires_explicit_finality_basis(
        self,
    ):
        api = self._api()

        store = FakeStore(
            _index_snapshot()
        )

        app = api.create_app(
            store=store
        )

        query = urlencode(
            {
                "chain_id": (
                    CHAIN_ID
                ),
                "contract_address": (
                    CONTRACT_ADDRESS
                ),
            }
        )

        status, _body = _request(
            app,
            path="/api/v1/index",
            query=query,
        )

        self.assertEqual(
            status,
            422,
        )

        self.assertEqual(
            store.loads,
            0,
        )

    def test_index_query_reads_one_durable_snapshot_and_preserves_provenance(
        self,
    ):
        api = self._api()

        store = FakeStore(
            _index_snapshot()
        )

        before = deepcopy(
            store.snapshot
        )

        app = api.create_app(
            store=store
        )

        query = urlencode(
            {
                "chain_id": (
                    CHAIN_ID
                ),
                "contract_address": (
                    CONTRACT_ADDRESS
                ),
                "state_basis": (
                    "FINALIZED"
                ),
            }
        )

        status, body = _request(
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
            body[
                "state_basis"
            ],
            "FINALIZED",
        )

        self.assertIsInstance(
            body[
                "source_payload_digest"
            ],
            str,
        )

        self.assertEqual(
            len(
                body[
                    "source_payload_digest"
                ]
            ),
            64,
        )

        self.assertEqual(
            store.loads,
            1,
        )

        self.assertEqual(
            store.snapshot,
            before,
        )

    def test_transaction_query_reads_one_durable_snapshot(
        self,
    ):
        api = self._api()

        store = FakeStore(
            _transaction_snapshot()
        )

        app = api.create_app(
            store=store
        )

        status, body = _request(
            app,
            path=(
                "/api/v1/transactions/"
                + TX_ID
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
            body[
                "status_name"
            ],
            "Finalized",
        )

        self.assertIs(
            body[
                "final_success"
            ],
            True,
        )

        self.assertIsNone(
            body[
                "application_decision"
            ]
        )

        self.assertEqual(
            store.loads,
            1,
        )

    def test_not_found_is_explicit_200_projection(
        self,
    ):
        api = self._api()

        store = FakeStore(
            _empty_snapshot()
        )

        app = api.create_app(
            store=store
        )

        query = urlencode(
            {
                "chain_id": (
                    CHAIN_ID
                ),
                "contract_address": (
                    CONTRACT_ADDRESS
                ),
                "state_basis": (
                    "FINALIZED"
                ),
            }
        )

        status, body = _request(
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
            False,
        )

        self.assertEqual(
            body[
                "requested_state_basis"
            ],
            "FINALIZED",
        )

    def test_corrupt_or_unavailable_storage_fails_closed(
        self,
    ):
        api = self._api()

        store = FakeStore(
            _empty_snapshot(),
            error=StorageCorruptionError(
                "secret database details"
            ),
        )

        app = api.create_app(
            store=store
        )

        query = urlencode(
            {
                "chain_id": (
                    CHAIN_ID
                ),
                "contract_address": (
                    CONTRACT_ADDRESS
                ),
                "state_basis": (
                    "FINALIZED"
                ),
            }
        )

        status, body = _request(
            app,
            path="/api/v1/index",
            query=query,
        )

        self.assertEqual(
            status,
            503,
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

        self.assertNotIn(
            "secret",
            json.dumps(
                body
            ).lower(),
        )

    def test_service_module_has_no_live_rpc_or_ingestion_coupling(
        self,
    ):
        self._api()

        source = Path(
            "backend/service_api.py"
        ).read_text()

        forbidden = (
            "backend.network_adapter",
            "build_network_index_observation",
            "classify_transaction_observation",
            "genlayer",
            "gen_call",
            "requests",
            "httpx",
        )

        for term in forbidden:
            self.assertNotIn(
                term,
                source,
            )


if __name__ == "__main__":
    unittest.main()
