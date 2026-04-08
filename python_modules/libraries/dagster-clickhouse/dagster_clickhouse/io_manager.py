from abc import abstractmethod
from collections.abc import Sequence
from typing import Any

from dagster import IOManagerDefinition, io_manager
from dagster._config.pythonic_config import ConfigurableIOManagerFactory
from dagster._core.storage.db_io_manager import DbIOManager, DbTypeHandler
from dagster._core.storage.io_manager import dagster_maintained_io_manager
from pydantic import Field

from dagster_clickhouse.db_client import ClickhouseDbClient


def build_clickhouse_io_manager(
    type_handlers: Sequence[DbTypeHandler], default_load_type: type | None = None
) -> IOManagerDefinition:
    """Builds an IO manager definition that reads inputs from and writes outputs to ClickHouse.

    ``TableSlice.schema`` is mapped to a ClickHouse **database** name (not a separate schema layer).

    Args:
        type_handlers: Handlers defining how to translate between ClickHouse tables and in-memory
            types (e.g. a Pandas ``DataFrame``). If only one handler is provided, it becomes the
            default load type when no annotation is present.
        default_load_type: Type to use when an input has no type annotation.

    Returns:
        IOManagerDefinition

    """

    @dagster_maintained_io_manager
    @io_manager(config_schema=ClickhouseIOManager.to_config_schema())
    def clickhouse_io_manager(init_context):
        return DbIOManager(
            type_handlers=type_handlers,
            db_client=ClickhouseDbClient(),
            io_manager_name="ClickhouseIOManager",
            database=init_context.resource_config["database"],
            schema=init_context.resource_config.get("schema"),
            default_load_type=default_load_type,
        )

    return clickhouse_io_manager


class ClickhouseIOManager(ConfigurableIOManagerFactory):
    """Base class for an IO manager that reads inputs from and writes outputs to ClickHouse.

    Asset and op metadata ``schema`` (and the I/O manager ``schema`` config) refer to the ClickHouse
    **database** that contains the table.

    The ``database`` field is the default database **on the ClickHouse connection** (server-side),
    not the database that qualifies table names in Dagster metadata (that is ``schema``).

    Examples:
        Subclass and implement ``type_handlers()`` with handlers from ``dagster-clickhouse-pandas``
        or ``dagster-clickhouse-polars``.

    """

    host: str = Field(description="ClickHouse server host.")
    port: int = Field(default=9000, description="Native protocol port (default 9000).")
    user: str = Field(default="default", description="User name.")
    password: str = Field(default="", description="Password.")
    database: str = Field(
        default="default",
        description=(
            "Default database on the ClickHouse connection (server-side). Table locations use the"
            " Dagster ``schema`` / asset metadata, which maps to a ClickHouse database name."
        ),
    )
    secure: bool = Field(default=False, description="Use TLS for the native protocol connection.")
    settings: dict[str, Any] = Field(
        default_factory=dict,
        description="Optional ClickHouse server settings passed to the driver client.",
    )
    schema_: str | None = Field(
        default=None,
        alias="schema",
        description="Default ClickHouse database for assets when not specified on the asset or op.",
    )

    @staticmethod
    @abstractmethod
    def type_handlers() -> Sequence[DbTypeHandler]: ...

    @staticmethod
    def default_load_type() -> type | None:
        return None

    def create_io_manager(self, context) -> DbIOManager:
        return DbIOManager(
            db_client=ClickhouseDbClient(),
            database=self.database,
            schema=self.schema_,
            type_handlers=self.type_handlers(),
            default_load_type=self.default_load_type(),
            io_manager_name="ClickhouseIOManager",
        )
