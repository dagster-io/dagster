from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime
from functools import reduce
from operator import and_
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
from ibis import _
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
        schema_list = connection.list_databases()
        if table_slice.schema not in schema_list:
            connection.create_database(table_slice.schema)

    @staticmethod
    def get_select_statement(table_slice: TableSlice) -> str:
        # Because we don't have access to the actual table here, we need
        # to create a fake table based on the columns and known types to
        # generate a select statement. This is a workaround that may not
        # reflect the actual SQL query that will be run on the database.
        schema = {col: str for col in table_slice.columns} if table_slice.columns else {}
        if table_slice.partition_dimensions:
            for partition_dimension in table_slice.partition_dimensions:
                schema[partition_dimension.partition_expr] = (
                    datetime if isinstance(partition_dimension.partitions, TimeWindow) else str
                )

        t = ibis.table(schema, table_slice.table, database=table_slice.schema)

        if table_slice.columns:
            t = t.select(table_slice.columns)

        if table_slice.partition_dimensions:
            t = t.filter(_partition_where_clause(table_slice.partition_dimensions))

        return str(ibis.to_sql(t))

    @staticmethod
    @contextmanager
    def connect(context, table_slice: TableSlice) -> Iterator[Any]:
        """Connect to the database using the specified Ibis backend."""
        # Create a copy of the resource_config without the 'backend' and
        # 'schema' parameters, and create an Ibis client for the backend
        config = deepcopy(context.resource_config)
        backend = getattr(ibis, config.pop("backend"))
        del config["schema"]
        con = backend.connect(**config)

        try:
            yield con
        finally:
            # Close connection if needed
            con.disconnect()


def _partition_where_clause(partition_dimensions: Sequence[TablePartitionDimension]) -> str:
    return reduce(
        and_,
        [
            (
                _time_window_where_clause(partition_dimension)
                if isinstance(partition_dimension.partitions, TimeWindow)
                else _static_where_clause(partition_dimension)
            )
            for partition_dimension in partition_dimensions
        ],
    )


def _time_window_where_clause(table_partition: TablePartitionDimension) -> ir.BooleanValue:
    partition = cast("TimeWindow", table_partition.partitions)
    start_dt, end_dt = partition
    return (_[table_partition.partition_expr] >= start_dt) & (
        _[table_partition.partition_expr] < end_dt
    )


def _static_where_clause(table_partition: TablePartitionDimension) -> ir.BooleanValue:
    return _[table_partition.partition_expr].isin(table_partition.partitions)
