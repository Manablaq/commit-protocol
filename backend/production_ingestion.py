from __future__ import annotations

from collections.abc import Mapping
from urllib.parse import urlsplit

from backend.ingestion_runner import (
    ingest_index_observation,
    ingest_transaction_observation,
)
from backend.postgres_driver import (
    PostgresAtomicDriver,
)
from backend.production_live_reader import (
    build_production_live_reader,
)
from backend.storage_adapter import (
    DurableStateStore,
)


PRODUCTION_INGESTION_SCHEMA = (
    "commit-production-ingestion-v1"
)

DATABASE_URL_ENV = (
    "DATABASE_URL"
)

STATE_NAMESPACE_ENV = (
    "COMMIT_STATE_NAMESPACE"
)

RPC_URL_ENV = (
    "GENLAYER_RPC_URL"
)

CONTRACT_ADDRESS_ENV = (
    "COMMIT_CONTRACT_ADDRESS"
)

SENDER_ADDRESS_ENV = (
    "COMMIT_READER_SENDER_ADDRESS"
)


class ProductionIngestionError(
    RuntimeError
):
    """Production ingestion composition failed safely."""


def _require_environment(
    environ,
):
    if not isinstance(
        environ,
        Mapping,
    ):
        raise ProductionIngestionError(
            "production ingestion configuration is invalid"
        )

    return environ


def _require_nonempty_text(
    value,
):
    if (
        type(value) is not str
        or not value.strip()
    ):
        raise ProductionIngestionError(
            "production ingestion configuration is invalid"
        )

    return value


def _require_rpc_url(
    value,
):
    value = _require_nonempty_text(
        value
    )

    try:
        parsed = urlsplit(
            value
        )
    except Exception:
        raise ProductionIngestionError(
            "production ingestion configuration is invalid"
        ) from None

    if (
        parsed.scheme
        not in (
            "http",
            "https",
        )
        or not parsed.hostname
    ):
        raise ProductionIngestionError(
            "production ingestion configuration is invalid"
        )

    return value


def _require_address(
    value,
):
    if (
        type(value) is not str
        or len(value) != 42
        or not value.startswith(
            "0x"
        )
    ):
        raise ProductionIngestionError(
            "production ingestion configuration is invalid"
        )

    try:
        int(
            value[
                2:
            ],
            16,
        )
    except ValueError:
        raise ProductionIngestionError(
            "production ingestion configuration is invalid"
        ) from None

    return value


class ProductionIngestion:
    def __init__(
        self,
        *,
        store,
        reader,
        contract_address,
    ):
        if store is None:
            raise ProductionIngestionError(
                "production ingestion store is invalid"
            )

        if reader is None:
            raise ProductionIngestionError(
                "production ingestion reader is invalid"
            )

        self._store = store
        self._reader = reader
        self._contract_address = (
            _require_address(
                contract_address
            )
        )

    def ingest_index(
        self,
        *,
        chain_id,
        block_number,
        state_status,
    ):
        return ingest_index_observation(
            store=self._store,
            reader=self._reader,
            chain_id=chain_id,
            contract_address=(
                self._contract_address
            ),
            block_number=block_number,
            state_status=state_status,
        )

    def ingest_transaction(
        self,
        *,
        genlayer_tx_id,
    ):
        receipt = (
            self._reader.get_transaction_receipt(
                genlayer_tx_id=(
                    genlayer_tx_id
                )
            )
        )

        if type(receipt) is not dict:
            raise ProductionIngestionError(
                "transaction receipt is invalid"
            )

        required_keys = (
            "genlayer_tx_id",
            "status_code",
            "status_name",
            "execution_result",
        )

        for key in required_keys:
            if key not in receipt:
                raise ProductionIngestionError(
                    "transaction receipt is invalid"
                )

        if (
            receipt[
                "genlayer_tx_id"
            ]
            != genlayer_tx_id
        ):
            raise ProductionIngestionError(
                "transaction receipt is invalid"
            )

        return ingest_transaction_observation(
            store=self._store,
            genlayer_tx_id=(
                receipt[
                    "genlayer_tx_id"
                ]
            ),
            status_code=(
                receipt[
                    "status_code"
                ]
            ),
            status_name=(
                receipt[
                    "status_name"
                ]
            ),
            execution_result=(
                receipt[
                    "execution_result"
                ]
            ),
        )


def build_production_ingestion(
    *,
    environ,
    connect,
):
    configuration = (
        _require_environment(
            environ
        )
    )

    if not callable(
        connect
    ):
        raise ProductionIngestionError(
            "production ingestion database connector is invalid"
        )

    database_url = (
        _require_nonempty_text(
            configuration.get(
                DATABASE_URL_ENV
            )
        )
    )

    namespace = (
        _require_nonempty_text(
            configuration.get(
                STATE_NAMESPACE_ENV
            )
        )
    )

    _require_rpc_url(
        configuration.get(
            RPC_URL_ENV
        )
    )

    contract_address = (
        _require_address(
            configuration.get(
                CONTRACT_ADDRESS_ENV
            )
        )
    )

    _require_address(
        configuration.get(
            SENDER_ADDRESS_ENV
        )
    )

    try:
        driver = PostgresAtomicDriver(
            database_url=database_url,
            connect=connect,
        )

        store = DurableStateStore(
            driver=driver,
            namespace=namespace,
        )

        reader = (
            build_production_live_reader(
                environ=configuration
            )
        )

        return ProductionIngestion(
            store=store,
            reader=reader,
            contract_address=(
                contract_address
            ),
        )

    except ProductionIngestionError:
        raise

    except Exception:
        raise ProductionIngestionError(
            "production ingestion composition failed"
        ) from None
