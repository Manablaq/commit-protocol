from __future__ import annotations

from collections.abc import Mapping
from urllib.parse import urlsplit

import eth_utils

from genlayer_py.abi import calldata
from genlayer_py.abi.transactions import serialize
from genlayer_py.contracts.utils import (
    make_calldata_object,
)
from genlayer_py.provider.provider import (
    GenLayerProvider,
)

from backend.live_reader import (
    GenLayerPinnedReader,
)


PRODUCTION_LIVE_READER_SCHEMA = (
    "commit-production-live-reader-v1"
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


class ProductionLiveReaderError(
    RuntimeError
):
    """Production reader composition failed safely."""


def _require_environment(
    environ,
):
    if not isinstance(
        environ,
        Mapping,
    ):
        raise ProductionLiveReaderError(
            "production reader configuration is invalid"
        )

    return environ


def _require_rpc_url(
    value,
) -> str:
    if (
        type(value) is not str
        or not value.strip()
    ):
        raise ProductionLiveReaderError(
            "production reader RPC configuration is invalid"
        )

    try:
        parsed = urlsplit(
            value
        )
    except Exception:
        raise ProductionLiveReaderError(
            "production reader RPC configuration is invalid"
        ) from None

    if (
        parsed.scheme
        not in (
            "http",
            "https",
        )
        or not parsed.hostname
    ):
        raise ProductionLiveReaderError(
            "production reader RPC configuration is invalid"
        )

    return value


def _require_address(
    value,
) -> str:
    if (
        type(value) is not str
        or len(value) != 42
        or not value.startswith(
            "0x"
        )
    ):
        raise ProductionLiveReaderError(
            "production reader address configuration is invalid"
        )

    try:
        int(
            value[
                2:
            ],
            16,
        )
    except ValueError:
        raise ProductionLiveReaderError(
            "production reader address configuration is invalid"
        ) from None

    return value


def _encode_call(
    *,
    function_name,
    args,
):
    call_object = make_calldata_object(
        method=function_name,
        args=args,
        kwargs=None,
    )

    encoded_call = calldata.encode(
        call_object
    )

    return serialize(
        [
            encoded_call,
            b"\x00",
        ]
    )


def _decode_result(
    *,
    raw_result,
):
    prefixed_result = (
        "0x"
        + raw_result
    )

    decoded_bytes = (
        eth_utils.hexadecimal.decode_hex(
            prefixed_result
        )
    )

    return calldata.decode(
        decoded_bytes
    )


def build_production_live_reader(
    *,
    environ,
):
    configuration = (
        _require_environment(
            environ
        )
    )

    rpc_url = _require_rpc_url(
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

    sender_address = (
        _require_address(
            configuration.get(
                SENDER_ADDRESS_ENV
            )
        )
    )

    try:
        provider = GenLayerProvider(
            rpc_url
        )
    except Exception:
        raise ProductionLiveReaderError(
            "production reader provider construction failed"
        ) from None

    try:
        return GenLayerPinnedReader(
            make_request=(
                provider.make_request
            ),
            contract_address=(
                contract_address
            ),
            sender_address=(
                sender_address
            ),
            encode_call=(
                _encode_call
            ),
            decode_result=(
                _decode_result
            ),
        )
    except Exception:
        raise ProductionLiveReaderError(
            "production reader construction failed"
        ) from None
