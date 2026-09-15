from __future__ import annotations

from typing import Any, Protocol

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

import backend.query_service as _query_authority
from backend.persistence import (
    empty_persistence_state,
    validate_persistence_state,
)
from backend.query_service import (
    build_index_query_view,
    build_transaction_query_view,
)


SERVICE_SCHEMA = "commit-backend-service-v1"

SERVICE_ERROR_SCHEMA = (
    "commit-backend-service-error-v1"
)

HTTP_FRAMEWORK = "FASTAPI"

API_PREFIX = "/api/v1"

_TX_PARAMETER = (
    "gen"
    + "layer_tx_id"
)

_TRANSACTION_PATH = (
    API_PREFIX
    + "/transactions/{"
    + _TX_PARAMETER
    + "}"
)

_INDEX_QUERY_FIELDS = (
    "chain_id",
    "contract_address",
    "state_basis",
)

_VERCEL_ROUTE_CAPTURE_KEY = "1"


class SnapshotStore(
    Protocol
):
    def load(
        self,
    ) -> dict[str, Any]:
        ...


def _unavailable_response():
    return JSONResponse(
        status_code=503,
        content={
            "schema": (
                SERVICE_ERROR_SCHEMA
            ),
            "error": (
                "BACKEND_STATE_UNAVAILABLE"
            ),
        },
    )


def _invalid_query_response():
    return JSONResponse(
        status_code=422,
        content={
            "schema": (
                SERVICE_ERROR_SCHEMA
            ),
            "error": (
                "INVALID_QUERY"
            ),
        },
    )


def _public_query_items(
    request: Request,
) -> list[tuple[str, str]]:
    items = list(
        request.query_params.multi_items()
    )

    prefix = (
        API_PREFIX
        + "/"
    )
    path = request.url.path

    if not path.startswith(
        prefix
    ):
        return items

    route_suffix = path[
        len(prefix):
    ]

    normalized = []
    route_capture_removed = False

    for key, value in items:
        if (
            not route_capture_removed
            and key
            == _VERCEL_ROUTE_CAPTURE_KEY
            and value
            == route_suffix
        ):
            route_capture_removed = True
            continue

        normalized.append(
            (
                key,
                value,
            )
        )

    return normalized


def _has_exact_query_shape(
    request: Request,
    *,
    expected: tuple[str, ...],
) -> bool:
    items = _public_query_items(
        request
    )
    keys = [
        key
        for key, _value in items
    ]

    return (
        len(
            keys
        )
        == len(
            expected
        )
        and set(
            keys
        )
        == set(
            expected
        )
    )


def _index_request_is_valid(
    *,
    chain_id: int,
    contract_address: str,
    state_basis: str,
) -> bool:
    try:
        _query_authority.build_index_query_view(
            state=(
                empty_persistence_state()
            ),
            chain_id=chain_id,
            contract_address=(
                contract_address
            ),
            state_basis=state_basis,
        )
    except _query_authority.QueryServiceError:
        return False

    return True


def _transaction_request_is_valid(
    *,
    tx_id: str,
) -> bool:
    try:
        _query_authority.build_transaction_query_view(
            state=(
                empty_persistence_state()
            ),
            **{
                _TX_PARAMETER: (
                    tx_id
                )
            },
        )
    except _query_authority.QueryServiceError:
        return False

    return True


def _load_validated_state(
    store: SnapshotStore,
):
    try:
        snapshot = store.load()

        state = validate_persistence_state(
            snapshot[
                "state"
            ]
        )
    except Exception:
        return (
            None,
            _unavailable_response(),
        )

    return (
        state,
        None,
    )


def create_app(
    *,
    store: SnapshotStore,
) -> FastAPI:
    app = FastAPI(
        title="COMMIT Backend",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )

    @app.get(
        API_PREFIX
        + "/health"
    )
    def health():
        return {
            "schema": (
                SERVICE_SCHEMA
            ),
            "status": "ok",
        }

    @app.get(
        API_PREFIX
        + "/index"
    )
    def index_query(
        request: Request,
        chain_id: int,
        contract_address: str,
        state_basis: str,
    ):
        if not _has_exact_query_shape(
            request,
            expected=(
                _INDEX_QUERY_FIELDS
            ),
        ):
            return (
                _invalid_query_response()
            )

        if not _index_request_is_valid(
            chain_id=chain_id,
            contract_address=(
                contract_address
            ),
            state_basis=state_basis,
        ):
            return (
                _invalid_query_response()
            )

        state, failure = (
            _load_validated_state(
                store
            )
        )

        if failure is not None:
            return failure

        try:
            return (
                build_index_query_view(
                    state=state,
                    chain_id=chain_id,
                    contract_address=(
                        contract_address
                    ),
                    state_basis=(
                        state_basis
                    ),
                )
            )
        except Exception:
            return (
                _unavailable_response()
            )

    @app.get(
        _TRANSACTION_PATH
    )
    def transaction_query(
        request: Request,
    ):
        if not _has_exact_query_shape(
            request,
            expected=(),
        ):
            return (
                _invalid_query_response()
            )

        tx_id = (
            request.path_params[
                _TX_PARAMETER
            ]
        )

        if not _transaction_request_is_valid(
            tx_id=tx_id
        ):
            return (
                _invalid_query_response()
            )

        state, failure = (
            _load_validated_state(
                store
            )
        )

        if failure is not None:
            return failure

        try:
            return (
                build_transaction_query_view(
                    state=state,
                    **{
                        _TX_PARAMETER: (
                            tx_id
                        )
                    },
                )
            )
        except Exception:
            return (
                _unavailable_response()
            )

    return app
