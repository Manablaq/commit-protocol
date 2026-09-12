from __future__ import annotations

from backend.postgres_driver import (
    SCHEMA_SQL,
)


SCHEMA_BOOTSTRAP_SCHEMA = (
    "commit-schema-bootstrap-v1"
)

DATABASE_URL_ENV = (
    "DATABASE_URL"
)


class SchemaBootstrapError(
    RuntimeError
):
    """Schema bootstrap failed safely."""


def _database_url(
    environ,
) -> str:
    try:
        value = environ[
            DATABASE_URL_ENV
        ]
    except (
        KeyError,
        TypeError,
        AttributeError,
    ):
        raise SchemaBootstrapError(
            "required schema bootstrap configuration is missing"
        ) from None

    if (
        type(value) is not str
        or value == ""
        or "\x00" in value
    ):
        raise SchemaBootstrapError(
            "required schema bootstrap configuration is invalid"
        )

    return value


def bootstrap_schema(
    *,
    environ,
    connect,
):
    database_url = _database_url(
        environ
    )

    if not callable(
        connect
    ):
        raise SchemaBootstrapError(
            "schema bootstrap connection factory is invalid"
        )

    try:
        with connect(
            database_url,
            autocommit=True,
        ) as connection:
            connection.execute(
                SCHEMA_SQL
            )
    except Exception:
        raise SchemaBootstrapError(
            "schema bootstrap execution failed"
        ) from None
