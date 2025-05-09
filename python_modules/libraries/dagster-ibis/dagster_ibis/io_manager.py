from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from typing import Any, Optional, cast

import ibis
import ibis.expr.types as ir
from dagster import OutputContext
from dagster._config.pythonic_config import ConfigurableIOManagerFactory
from dagster._core.definitions.time_window_partitions import TimeWindow
from dagster._core.storage.db_io_manager import (
    DbClient,
    DbIOManager,
    DbTypeHandler,
    TablePartitionDimension,
    TableSlice,
)
from pydantic import Field


class IbisIOManager(ConfigurableIOManagerFactory):
    """An IO manager for reading from and writing to databases using Ibis.

    This IO manager integrates Dagster with Ibis, allowing you to read and write data
    using Ibis's unified interface to many database backends.

    Examples:
        .. code-block:: python

            from dagster import Definitions, asset
            from dagster_ibis import IbisIOManager
            import ibis
            import ibis.expr.types as ir
            import pandas as pd

            @asset
            def my_table() -> ir.Table:  # the name of the asset will be the table name
                # Create an Ibis table
                df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
                return ibis.memtable(df)

            defs = Definitions(
                assets=[my_table],
                resources={
                    "io_manager": IbisIOManager(
                        backend="duckdb",
                        database="my_db.duckdb",
                        schema="my_schema"
                    )
                }
            )
    """

    backend: str = Field(
        description="The Ibis backend to use (e.g., 'duckdb', 'sqlite', 'postgres', etc.)"
    )
    schema_: Optional[str] = Field(
        default=None, alias="schema", description="Name of the schema to use."
    )  # schema is a reserved word for pydantic

    # Additional connection parameters will be captured as extra fields
    model_config = {
        "extra": "allow",  # Allow extra fields not defined in the model
    }

    @staticmethod
    def type_handlers() -> Sequence[DbTypeHandler]:
        from dagster_ibis.ibis_type_handler import IbisTypeHandler

        return [IbisTypeHandler()]

    @staticmethod
    def default_load_type() -> Optional[type]:
        return ir.Table

    def create_io_manager(self, context) -> DbIOManager:
        return DbIOManager(
            db_client=IbisClient(),
            database=getattr(self, "database", None),
            schema=self.schema_,
            type_handlers=self.type_handlers(),
            default_load_type=self.default_load_type(),
            io_manager_name="IbisIOManager",
        )


class IbisClient(DbClient):
    @staticmethod
    def delete_table_slice(context: OutputContext, table_slice: TableSlice, connection) -> None:
        try:
            # For partitioned data, we only want to delete the specific partition
            if table_slice.partition_dimensions:
                query = f"DELETE FROM {table_slice.schema}.{table_slice.table} WHERE\n"
                where_clause = _partition_where_clause(table_slice.partition_dimensions)
                connection.raw_sql(query + where_clause)
            else:
                connection.drop_table(table_slice.table, schema=table_slice.schema, force=True)
        except Exception:
            # Table might not exist yet, so ignore errors
            pass

    @staticmethod
    def ensure_schema_exists(context: OutputContext, table_slice: TableSlice, connection) -> None:
        schema_list = connection.list_schemas()
        if table_slice.schema not in schema_list:
            connection.create_schema(table_slice.schema)

    @staticmethod
    def get_select_statement(table_slice: TableSlice) -> str:
        qualified_name = f"{table_slice.schema}.{table_slice.table}"

        if table_slice.columns:
            cols = ", ".join(table_slice.columns)
            select_stmt = f"SELECT {cols} FROM {qualified_name}"
        else:
            select_stmt = f"SELECT * FROM {qualified_name}"

        if table_slice.partition_dimensions:
            select_stmt += " WHERE " + _partition_where_clause(table_slice.partition_dimensions)

        return select_stmt

    @staticmethod
    @contextmanager
    def connect(context, table_slice: TableSlice) -> Iterator[Any]:
        """Connect to the database using the specified Ibis backend."""
        # Get the backend from context config
        backend = context.resource_config["backend"]

        # Create a copy of the resource_config without the 'backend' parameter
        # We need to be careful as config might contain schema which is a reserved keyword
        config_params = {}
        for k, v in context.resource_config.items():
            if k not in ["backend", "schema_"]:
                config_params[k] = v

        # If schema is defined in resource_config as schema_, map it to schema
        if "schema_" in context.resource_config:
            config_params["schema"] = context.resource_config["schema_"]

        # Get the backend module (e.g., ibis.duckdb, ibis.sqlite, etc.)
        backend_module = getattr(ibis, backend)

        # Connect to the database using the backend's connect method
        conn = backend_module.connect(**config_params)

        try:
            yield conn
        finally:
            # Close connection if needed
            if hasattr(conn, "close"):
                conn.close()


def _partition_where_clause(partition_dimensions: Sequence[TablePartitionDimension]) -> str:
    return " AND ".join(
        (
            _time_window_where_clause(partition_dimension)
            if isinstance(partition_dimension.partitions, TimeWindow)
            else _static_where_clause(partition_dimension)
        )
        for partition_dimension in partition_dimensions
    )


def _time_window_where_clause(table_partition: TablePartitionDimension) -> str:
    partition = cast("TimeWindow", table_partition.partitions)
    start_dt, end_dt = partition
    start_dt_str = start_dt.strftime("%Y-%m-%d %H:%M:%S")
    end_dt_str = end_dt.strftime("%Y-%m-%d %H:%M:%S")
    return f"""{table_partition.partition_expr} >= '{start_dt_str}' AND {table_partition.partition_expr} < '{end_dt_str}'"""


def _static_where_clause(table_partition: TablePartitionDimension) -> str:
    partitions = ", ".join(f"'{partition}'" for partition in table_partition.partitions)
    return f"""{table_partition.partition_expr} in ({partitions})"""
