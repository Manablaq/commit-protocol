from __future__ import annotations

import argparse
import os
import sys

import psycopg

from backend.production_ingestion import (
    build_production_ingestion,
)


OPERATOR_SCHEMA = (
    "commit-production-ingestion-operator-v1"
)

MODE_INDEX = "index"
MODE_TRANSACTION = "transaction"

EXIT_SUCCESS = 0
EXIT_FAILURE = 1
EXIT_USAGE = 2


def _build_parser():
    parser = argparse.ArgumentParser(
        prog="run_backend_ingestion",
    )

    modes = parser.add_subparsers(
        dest="mode",
        required=True,
    )

    index_parser = modes.add_parser(
        MODE_INDEX
    )

    index_parser.add_argument(
        "--chain-id",
        required=True,
        type=int,
    )

    index_parser.add_argument(
        "--block-number",
        required=True,
        type=int,
    )

    index_parser.add_argument(
        "--state-status",
        required=True,
        choices=(
            "accepted",
            "finalized",
        ),
    )

    transaction_parser = modes.add_parser(
        MODE_TRANSACTION
    )

    transaction_parser.add_argument(
        "--genlayer-tx-id",
        required=True,
    )

    return parser


def _parse_arguments(
    argv,
):
    parser = _build_parser()

    try:
        arguments = parser.parse_args(
            argv
        )
    except SystemExit:
        return None
    except Exception:
        return None

    if (
        arguments.mode
        == MODE_INDEX
    ):
        if (
            type(
                arguments.chain_id
            )
            is not int
            or arguments.chain_id <= 0
            or type(
                arguments.block_number
            )
            is not int
            or arguments.block_number < 0
        ):
            return None

    if (
        arguments.mode
        == MODE_TRANSACTION
    ):
        if (
            type(
                arguments.genlayer_tx_id
            )
            is not str
            or not arguments.genlayer_tx_id.strip()
        ):
            return None

    return arguments


def main(
    *,
    argv,
    environ,
    connect,
):
    arguments = _parse_arguments(
        argv
    )

    if arguments is None:
        return EXIT_USAGE

    try:
        composition = (
            build_production_ingestion(
                environ=environ,
                connect=connect,
            )
        )

        if (
            arguments.mode
            == MODE_INDEX
        ):
            composition.ingest_index(
                chain_id=(
                    arguments.chain_id
                ),
                block_number=(
                    arguments.block_number
                ),
                state_status=(
                    arguments.state_status
                ),
            )

        elif (
            arguments.mode
            == MODE_TRANSACTION
        ):
            composition.ingest_transaction(
                genlayer_tx_id=(
                    arguments.genlayer_tx_id
                ),
            )

        else:
            return EXIT_USAGE

    except Exception:
        print(
            "backend ingestion failed",
            file=sys.stderr,
        )

        return EXIT_FAILURE

    return EXIT_SUCCESS


if __name__ == "__main__":
    raise SystemExit(
        main(
            argv=sys.argv[1:],
            environ=os.environ,
            connect=psycopg.connect,
        )
    )
