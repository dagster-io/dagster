from abc import abstractmethod
from collections.abc import Sequence
from contextlib import contextmanager
from typing import Any, Optional, cast

import duckdb
from dagster import IOManagerDefinition, OutputContext, io_manager
from dagster._config.pythonic_config import ConfigurableIOManagerFactory
from dagster._core.definitions.time_window_partitions import TimeWindow
from dagster._core.storage.db_io_manager import (
    DbClient,
    DbIOManager,
    DbTypeHandler,
    TablePartitionDimension,
    TableSlice,
)
from dagster._core.storage.io_manager import dagster_maintained_io_manager
from dagster._utils.backoff import backoff
from packaging.version import Version
from pydantic import Field

DUCKDB_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


def build_duckdb_io_manager(
    type_handlers: Sequence[DbTypeHandler], default_load_type: Optional[type] = None
) -> IOManagerDefinition:
    """Builds an IO manager definition that reads inputs from and writes outputs to DuckDB.

    Args:
        type_handlers (Sequence[DbTypeHandler]): Each handler defines how to translate between
            DuckDB tables and an in-memory type - e.g. a Pandas DataFrame. If only
            one DbTypeHandler is provided, it will be used as teh default_load_type.
        default_load_type (Type): When an input has no type annotation, load it as this type.

    Returns:
        IOManagerDefinition

    Examples:
        .. code-block:: python

            from dagster_duckdb import build_duckdb_io_manager
            from dagster_duckdb_pandas import DuckDBPandasTypeHandler

            @asset(
                key_prefix=["my_schema"]  # will be used as the schema in duckdb
            )
            def my_table() -> pd.DataFrame:  # the name of the asset will be the table name
                ...

            duckdb_io_manager = build_duckdb_io_manager([DuckDBPandasTypeHandler()])

            defs = Definitions(
                assets=[my_table]
                resources={"io_manager" duckdb_io_manager.configured({"database": "my_db.duckdb"})}
            )

    You can set a default schema to store the assets using the ``schema`` configuration value of the DuckDB I/O
    Manager. This schema will be used if no other schema is specified directly on an asset or op.

    .. code-block:: python

        defs = Definitions(
            assets=[my_table]
            resources={"io_manager" duckdb_io_manager.configured(
                {"database": "my_db.duckdb", "schema": "my_schema"} # will be used as the schema
            )}
        )


    On individual assets, you an also specify the schema where they should be stored using metadata or
    by adding a ``key_prefix`` to the asset key. If both ``key_prefix`` and metadata are defined, the metadata will
    take precedence.

    .. code-block:: python

        @asset(
            key_prefix=["my_schema"]  # will be used as the schema in duckdb
        )
        def my_table() -> pd.DataFrame:
            ...

        @asset(
            metadata={"schema": "my_schema"}  # will be used as the schema in duckdb
        )
        def my_other_table() -> pd.DataFrame:
            ...

    For ops, the schema can be specified by including a "schema" entry in output metadata.

    .. code-block:: python

        @op(
            out={"my_table": Out(metadata={"schema": "my_schema"})}
        )
        def make_my_table() -> pd.DataFrame:
            ...

    If none of these is provided, the schema will default to "public".

    To only use specific columns of a table as input to a downstream op or asset, add the metadata "columns" to the
    In or AssetIn.

    .. code-block:: python

        @asset(
            ins={"my_table": AssetIn("my_table", metadata={"columns": ["a"]})}
        )
        def my_table_a(my_table: pd.DataFrame):
            # my_table will just contain the data from column "a"
            ...

    """

    @dagster_maintained_io_manager
    @io_manager(config_schema=DuckDBIOManager.to_config_schema())
    def duckdb_io_manager(init_context):
        """IO Manager for storing outputs in a DuckDB database.

        Assets will be stored in the schema and table name specified by their AssetKey.
        Subsequent materializations of an asset will overwrite previous materializations of that asset.
        Op outputs will be stored in the schema specified by output metadata (defaults to public) in a
        table of the name of the output.
        """
        return DbIOManager(
            type_handlers=type_handlers,
            db_client=DuckDbClient(),
            io_manager_name="DuckDBIOManager",
            database=init_context.resource_config["database"],
            schema=init_context.resource_config.get("schema"),
            default_load_type=default_load_type,
        )

    return duckdb_io_manager


class DuckDBIOManager(ConfigurableIOManagerFactory):
    """Base class for an IO manager definition that reads inputs from and writes outputs to DuckDB.

    Examples:
        .. code-block:: python

            from dagster_duckdb import DuckDBIOManager
            from dagster_duckdb_pandas import DuckDBPandasTypeHandler

            class MyDuckDBIOManager(DuckDBIOManager):
                @staticmethod
                def type_handlers() -> Sequence[DbTypeHandler]:
                    return [DuckDBPandasTypeHandler()]

            @asset(
                key_prefix=["my_schema"]  # will be used as the schema in duckdb
            )
            def my_table() -> pd.DataFrame:  # the name of the asset will be the table name
                ...

            defs = Definitions(
                assets=[my_table],
                resources={"io_manager": MyDuckDBIOManager(database="my_db.duckdb")}
            )

    You can set a default schema to store the assets using the ``schema`` configuration value of the DuckDB I/O
    Manager. This schema will be used if no other schema is specified directly on an asset or op.

    .. code-block:: python

        defs = Definitions(
            assets=[my_table],
            resources={"io_manager": MyDuckDBIOManager(database="my_db.duckdb", schema="my_schema")}
        )

    On individual assets, you an also specify the schema where they should be stored using metadata or
    by adding a ``key_prefix`` to the asset key. If both ``key_prefix`` and metadata are defined, the metadata will
    take precedence.

    .. code-block:: python

        @asset(
            key_prefix=["my_schema"]  # will be used as the schema in duckdb
        )
        def my_table() -> pd.DataFrame:
            ...

        @asset(
            metadata={"schema": "my_schema"}  # will be used as the schema in duckdb
        )
        def my_other_table() -> pd.DataFrame:
            ...

    For ops, the schema can be specified by including a "schema" entry in output metadata.

    .. code-block:: python

        @op(
            out={"my_table": Out(metadata={"schema": "my_schema"})}
        )
        def make_my_table() -> pd.DataFrame:
            ...

    If none of these is provided, the schema will default to "public".

    To only use specific columns of a table as input to a downstream op or asset, add the metadata "columns" to the
    In or AssetIn.

    .. code-block:: python

        @asset(
            ins={"my_table": AssetIn("my_table", metadata={"columns": ["a"]})}
        )
        def my_table_a(my_table: pd.DataFrame):
            # my_table will just contain the data from column "a"
            ...

    Set DuckDB configuration options using the connection_config field. See
    https://duckdb.org/docs/sql/configuration.html for all available settings.

    .. code-block:: python

        defs = Definitions(
            assets=[my_table],
            resources={"io_manager": MyDuckDBIOManager(database="my_db.duckdb",
                                                       connection_config={"arrow_large_buffer_size": True})}
        )

    """

    database: str = Field(description="Path to the DuckDB database.")
    connection_config: dict[str, Any] = Field(
        description=(
            "DuckDB connection configuration options. See"
            " https://duckdb.org/docs/sql/configuration.html"
        ),
        default={},
    )
    schema_: Optional[str] = Field(
        default=None, alias="schema", description="Name of the schema to use."
    )  # schema is a reserved word for pydantic

    @staticmethod
    @abstractmethod
    def type_handlers() -> Sequence[DbTypeHandler]: ...

    @staticmethod
    def default_load_type() -> Optional[type]:
        return None

    def create_io_manager(self, context) -> DbIOManager:
        return DbIOManager(
            db_client=DuckDbClient(),
            database=self.database,
            schema=self.schema_,
            type_handlers=self.type_handlers(),
            default_load_type=self.default_load_type(),
            io_manager_name="DuckDBIOManager",
        )


class DuckDbClient(DbClient):
    @staticmethod
    def delete_table_slice(context: OutputContext, table_slice: TableSlice, connection) -> None:
        try:
            connection.execute(_get_cleanup_statement(table_slice))
        except duckdb.CatalogException:
            # table doesn't exist yet, so ignore the error
            pass

    @staticmethod
    def ensure_schema_exists(context: OutputContext, table_slice: TableSlice, connection) -> None:
        connection.execute(f"create schema if not exists {table_slice.schema};")

    @staticmethod
    def get_select_statement(table_slice: TableSlice) -> str:
        col_str = ", ".join(table_slice.columns) if table_slice.columns else "*"

        if table_slice.partition_dimensions:
            query = f"SELECT {col_str} FROM {table_slice.schema}.{table_slice.table} WHERE\n"
            return query + _partition_where_clause(table_slice.partition_dimensions)
        else:
            return f"""SELECT {col_str} FROM {table_slice.schema}.{table_slice.table}"""

    @staticmethod
    @contextmanager
    def connect(context, _):  # pyright: ignore[reportIncompatibleMethodOverride]
        config = context.resource_config["connection_config"]

        # support for `custom_user_agent` was added in v1.0.0
        # https://github.com/duckdb/duckdb/commit/0c66b6007b736ed2197bca54d20c9ad9a5eeef46
        if Version(duckdb.__version__) >= Version("1.0.0"):
            config = {
                "custom_user_agent": "dagster",
                **config,
            }

        conn = backoff(
            fn=duckdb.connect,
            retry_on=(RuntimeError, duckdb.IOException),
            kwargs={
                "database": context.resource_config["database"],
                "read_only": False,
                "config": config,
            },
            max_retries=10,
        )

        yield conn

        conn.close()


def _get_cleanup_statement(table_slice: TableSlice) -> str:
    """Returns a SQL statement that deletes data in the given table to make way for the output data
    being written.
    """
    if table_slice.partition_dimensions:
        query = f"DELETE FROM {table_slice.schema}.{table_slice.table} WHERE\n"
        return query + _partition_where_clause(table_slice.partition_dimensions)
    else:
        return f"DELETE FROM {table_slice.schema}.{table_slice.table}"


def _partition_where_clause(partition_dimensions: Sequence[TablePartitionDimension]) -> str:
    return " AND\n".join(
        (
            _time_window_where_clause(partition_dimension)
            if isinstance(partition_dimension.partitions, TimeWindow)
            else _static_where_clause(partition_dimension)
        )
        for partition_dimension in partition_dimensions
    )


def _time_window_where_clause(table_partition: TablePartitionDimension) -> str:
    partition = cast(TimeWindow, table_partition.partitions)
    start_dt, end_dt = partition
    start_dt_str = start_dt.strftime(DUCKDB_DATETIME_FORMAT)
    end_dt_str = end_dt.strftime(DUCKDB_DATETIME_FORMAT)
    return f"""{table_partition.partition_expr} >= '{start_dt_str}' AND {table_partition.partition_expr} < '{end_dt_str}'"""


def _static_where_clause(table_partition: TablePartitionDimension) -> str:
    partitions = ", ".join(f"'{partition}'" for partition in table_partition.partitions)
    return f"""{table_partition.partition_expr} in ({partitions})"""
