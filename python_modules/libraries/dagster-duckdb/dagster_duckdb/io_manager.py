from typing import Sequence

import duckdb

from dagster import (
    DbClient,
    DbIOManager,
    DbTypeHandler,
    Field,
    IOManagerDefinition,
    OutputContext,
    TablePartition,
    TableSlice,
    io_manager,
)
from dagster._utils.backoff import backoff

DUCKDB_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


def build_duckdb_io_manager(type_handlers: Sequence[DbTypeHandler]) -> IOManagerDefinition:
    """
    Builds an IO manager definition that reads inputs from and writes outputs to DuckDB.

    Note that the DuckDBIOManager cannot load partitioned assets.

    Args:
        type_handlers (Sequence[DbTypeHandler]): Each handler defines how to translate between
            DuckDB tables and an in-memory type - e.g. a Pandas DataFrame.

    Returns:
        IOManagerDefinition

    Examples:

        .. code-block:: python

            from dagster_duckdb import build_duckdb_io_manager
            from dagster_duckdb_pandas import DuckDBPandasTypeHandler

            duckdb_io_manager = build_duckdb_io_manager([DuckDBPandasTypeHandler()])

            @job(resource_defs={'io_manager': duckdb_io_manager})
            def my_job():
                ...

    You may configure the returned IO Manager as follows:

    .. code-block:: YAML

        resources:
            io_manager:
                config:
                    base_path: path/to/store/files  # all data will be stored at this path
                    duckdb_path: path/to/database.duckdb  # path to the duckdb database
    """

    @io_manager(config_schema={"base_path": Field(str, is_required=False), "duckdb_path": str})
    def duckdb_io_manager(_):
        """IO Manager for storing outputs in a DuckDB database

        Supports storing and loading Pandas DataFrame objects. Converts the DataFrames to CSV and
        creates DuckDB views over the files.

        Assets will be stored in the schema and table name specified by their AssetKey.
        Subsequent materializations of an asset will overwrite previous materializations of that asset.
        Op outputs will be stored in the schema specified by output metadata (defaults to public) in a
        table of the name of the output.
        """
        return DbIOManager(
            type_handlers=type_handlers, db_client=DuckDbClient(), io_manager_name="DuckDBIOManager"
        )

    return duckdb_io_manager


class DuckDbClient(DbClient):
    @staticmethod
    def delete_table_slice(context: OutputContext, table_slice: TableSlice) -> None:
        conn = _connect_duckdb(context).cursor()
        try:
            conn.execute(_get_cleanup_statement(table_slice))
        except duckdb.CatalogException:
            # table doesn't exist yet, so ignore the error
            pass
        conn.close()

    @staticmethod
    def get_select_statement(table_slice: TableSlice) -> str:
        col_str = ", ".join(table_slice.columns) if table_slice.columns else "*"
        if table_slice.partition:
            return (
                f"SELECT {col_str} FROM {table_slice.schema}.{table_slice.table}\n"
                + _time_window_where_clause(table_slice.partition)
            )
        else:
            return f"""SELECT {col_str} FROM {table_slice.schema}.{table_slice.table}"""


def _connect_duckdb(context):
    return backoff(
        fn=duckdb.connect,
        retry_on=(RuntimeError, duckdb.IOException),
        kwargs={"database": context.resource_config["duckdb_path"], "read_only": False},
        max_retries=10,
    )


def _get_cleanup_statement(table_slice: TableSlice) -> str:
    """
    Returns a SQL statement that deletes data in the given table to make way for the output data
    being written.
    """
    if table_slice.partition:
        return (
            f"DELETE FROM {table_slice.schema}.{table_slice.table}\n"
            + _time_window_where_clause(table_slice.partition)
        )
    else:
        return f"DELETE FROM {table_slice.schema}.{table_slice.table}"


def _time_window_where_clause(table_partition: TablePartition) -> str:
    start_dt, end_dt = table_partition.time_window
    start_dt_str = start_dt.strftime(DUCKDB_DATETIME_FORMAT)
    end_dt_str = end_dt.strftime(DUCKDB_DATETIME_FORMAT)
    return f"""WHERE {table_partition.partition_expr} BETWEEN '{start_dt_str}' AND '{end_dt_str}'"""
