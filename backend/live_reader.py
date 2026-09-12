from __future__ import annotations


LIVE_READER_SCHEMA = (
    "commit-genlayer-live-reader-v1"
)

_ALLOWED_STATE_STATUSES = (
    "accepted",
    "finalized",
)


class LiveReaderError(
    RuntimeError
):
    """Pinned GenLayer read failed safely."""


def _require_callable(
    value,
):
    if not callable(
        value
    ):
        raise LiveReaderError(
            "live reader dependency is invalid"
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
        raise LiveReaderError(
            "live reader address is invalid"
        )

    try:
        int(
            value[
                2:
            ],
            16,
        )
    except ValueError:
        raise LiveReaderError(
            "live reader address is invalid"
        ) from None

    return value


def _require_transaction_id(
    value,
) -> str:
    if (
        type(value) is not str
        or len(value) != 66
        or not value.startswith(
            "0x"
        )
    ):
        raise LiveReaderError(
            "transaction identifier is invalid"
        )

    try:
        int(
            value[
                2:
            ],
            16,
        )
    except ValueError:
        raise LiveReaderError(
            "transaction identifier is invalid"
        ) from None

    return value


def _require_rpc_response(
    response,
):
    if type(response) is not dict:
        raise LiveReaderError(
            "RPC response is invalid"
        )

    if "result" not in response:
        raise LiveReaderError(
            "RPC response is invalid"
        )

    return response[
        "result"
    ]


class GenLayerPinnedReader:
    def __init__(
        self,
        *,
        make_request,
        contract_address,
        sender_address,
        encode_call,
        decode_result,
    ):
        self._make_request = (
            _require_callable(
                make_request
            )
        )

        self._contract_address = (
            _require_address(
                contract_address
            )
        )

        self._sender_address = (
            _require_address(
                sender_address
            )
        )

        self._encode_call = (
            _require_callable(
                encode_call
            )
        )

        self._decode_result = (
            _require_callable(
                decode_result
            )
        )

    def read_contract(
        self,
        *,
        function_name,
        args,
        block_number,
        state_status,
    ):
        if (
            type(function_name)
            is not str
            or function_name == ""
        ):
            raise LiveReaderError(
                "contract function name is invalid"
            )

        if type(args) is not tuple:
            raise LiveReaderError(
                "contract arguments are invalid"
            )

        if (
            type(block_number)
            is not int
            or block_number < 0
        ):
            raise LiveReaderError(
                "block number is invalid"
            )

        if (
            state_status
            not in _ALLOWED_STATE_STATUSES
        ):
            raise LiveReaderError(
                "state status is invalid"
            )

        try:
            encoded_call = (
                self._encode_call(
                    function_name=(
                        function_name
                    ),
                    args=args,
                )
            )
        except Exception:
            raise LiveReaderError(
                "contract call encoding failed"
            ) from None

        if (
            type(encoded_call)
            is not str
            or encoded_call == ""
        ):
            raise LiveReaderError(
                "contract call encoding failed"
            )

        try:
            response = (
                self._make_request(
                    method="gen_call",
                    params=[
                        {
                            "type": "read",
                            "from": (
                                self._sender_address
                            ),
                            "to": (
                                self._contract_address
                            ),
                            "data": (
                                encoded_call
                            ),
                            "blockNumber": (
                                hex(
                                    block_number
                                )
                            ),
                            "status": (
                                state_status
                            ),
                        },
                    ],
                )
            )
        except Exception:
            raise LiveReaderError(
                "contract read RPC failed"
            ) from None

        raw_result = (
            _require_rpc_response(
                response
            )
        )

        if type(raw_result) is not str:
            raise LiveReaderError(
                "contract read result is invalid"
            )

        try:
            return self._decode_result(
                raw_result=raw_result
            )
        except Exception:
            raise LiveReaderError(
                "contract read decoding failed"
            ) from None

    def get_transaction_receipt(
        self,
        *,
        genlayer_tx_id,
    ):
        transaction_id = (
            _require_transaction_id(
                genlayer_tx_id
            )
        )

        try:
            response = (
                self._make_request(
                    method=(
                        "gen_getTransactionReceipt"
                    ),
                    params=[
                        {
                            "txId": (
                                transaction_id
                            ),
                        },
                    ],
                )
            )
        except Exception:
            raise LiveReaderError(
                "transaction receipt RPC failed"
            ) from None

        receipt = (
            _require_rpc_response(
                response
            )
        )

        if type(receipt) is not dict:
            raise LiveReaderError(
                "transaction receipt is invalid"
            )

        receipt_id = receipt.get(
            "id"
        )

        status_code = receipt.get(
            "status"
        )

        status_name = receipt.get(
            "statusName"
        )

        execution_result = receipt.get(
            "txExecutionResultName"
        )

        if (
            type(receipt_id) is not str
            or receipt_id
            != transaction_id
        ):
            raise LiveReaderError(
                "transaction receipt identifier mismatch"
            )

        if type(status_code) is not int:
            raise LiveReaderError(
                "transaction receipt status is invalid"
            )

        if (
            type(status_name) is not str
            or status_name == ""
        ):
            raise LiveReaderError(
                "transaction receipt status is invalid"
            )

        if (
            type(execution_result)
            is not str
            or execution_result == ""
        ):
            raise LiveReaderError(
                "transaction execution result is invalid"
            )

        return {
            "genlayer_tx_id": (
                transaction_id
            ),
            "status_code": (
                status_code
            ),
            "status_name": (
                status_name
            ),
            "execution_result": (
                execution_result
            ),
        }
