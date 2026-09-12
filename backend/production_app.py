from __future__ import annotations

from typing import Any

from backend.postgres_driver import (
    PostgresAtomicDriver,
)
from backend.service_api import (
    create_app,
)
from backend.storage_adapter import (
    DurableStateStore,
)


PRODUCTION_COMPOSITION_SCHEMA = (
    "commit-production-composition-v1"
)

DATABASE_URL_ENV = (
    "DATABASE_URL"
)

STATE_NAMESPACE_ENV = (
    "COMMIT_STATE_NAMESPACE"
)


class ProductionCompositionError(
    RuntimeError
):
    """Invalid production composition configuration."""


def _required_text(
    environ: Any,
    *,
    key: str,
) -> str:
    try:
        value = environ[
            key
        ]
    except (
        KeyError,
        TypeError,
        AttributeError,
    ):
        raise ProductionCompositionError(
            "required production configuration is missing"
        ) from None

    if (
        type(value) is not str
        or value == ""
        or "\x00" in value
    ):
        raise ProductionCompositionError(
            "required production configuration is invalid"
        )

    return value


def build_production_app(
    *,
    environ,
    connect,
):
    database_url = _required_text(
        environ,
        key=DATABASE_URL_ENV,
    )

    namespace = _required_text(
        environ,
        key=STATE_NAMESPACE_ENV,
    )

    driver = PostgresAtomicDriver(
        database_url=database_url,
        connect=connect,
    )

    store = DurableStateStore(
        driver=driver,
        namespace=namespace,
    )

    return create_app(
        store=store,
    )
