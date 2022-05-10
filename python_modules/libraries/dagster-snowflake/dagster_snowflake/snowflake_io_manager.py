from typing import Sequence

from dagster import Field, IOManagerDefinition, OutputContext, StringSource, io_manager

from .db_io_manager import DbClient, DbIOManager, DbTypeHandler, TablePartition, TableSlice
from .resources import SnowflakeConnection

SNOWFLAKE_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


def build_snowflake_io_manager(type_handlers: Sequence[DbTypeHandler]) -> IOManagerDefinition:
    """
    Builds an IO manager definition that reads inputs from and writes outputs to Snowflake.

    Args:
        type_handlers (Sequence[DbTypeHandler]): Each handler defines how to translate between
            slices of Snowflake tables and an in-memory type - e.g. a Pandas DataFrame.

    Returns:
        IOManagerDefinition

    Examples:

        .. code-block:: python

            from dagster_snowflake import build_snowflake_io_manager
            from dagster_snowflake_pandas import SnowflakePandasTypeHandler

            snowflake_io_manager = build_snowflake_io_manager([SnowflakePandasTypeHandler()])

            @job(resource_defs={'io_manager': snowflake_io_manager})
            def my_job():
                ...
    """

    @io_manager(
        config_schema={
            "database": StringSource,
            "account": StringSource,
            "user": StringSource,
            "password": StringSource,
            "warehouse": Field(StringSource, is_required=False),
        }
    )
    def snowflake_io_manager():
        return DbIOManager(type_handlers=type_handlers, db_client=SnowflakeDbClient())

    return snowflake_io_manager


class SnowflakeDbClient(DbClient):
    @staticmethod
    def delete_table_slice(context: OutputContext, table_slice: TableSlice) -> None:
        with SnowflakeConnection(
            dict(**(context.resource_config or {}), schema=table_slice.schema), context.log
        ).get_connection() as con:
            con.execute(_get_cleanup_statement(table_slice))

    @staticmethod
    def get_select_statement(table_slice: TableSlice) -> str:
        col_str = ", ".join(table_slice.columns) if table_slice.columns else "*"
        if table_slice.partition:
            return (
                f"SELECT {col_str} FROM {table_slice.database}.{table_slice.schema}.{table_slice.table}\n"
                + _time_window_where_clause(table_slice.partition)
            )
        else:
            return f"""SELECT {col_str} FROM {table_slice.database}.{table_slice.schema}.{table_slice.table}"""


def _get_cleanup_statement(table_slice: TableSlice) -> str:
    """
    Returns a SQL statement that deletes data in the given table to make way for the output data
    being written.
    """
    if table_slice.partition:
        return (
            f"DELETE FROM {table_slice.database}.{table_slice.schema}.{table_slice.table}\n"
            + _time_window_where_clause(table_slice.partition)
        )
    else:
        return f"DELETE FROM {table_slice.database}.{table_slice.schema}.{table_slice.table}"


def _time_window_where_clause(table_partition: TablePartition) -> str:
    start_dt, end_dt = table_partition.time_window
    start_dt_str = start_dt.strftime(SNOWFLAKE_DATETIME_FORMAT)
    end_dt_str = end_dt.strftime(SNOWFLAKE_DATETIME_FORMAT)
    return f"""WHERE {table_partition.partition_expr} BETWEEN '{start_dt_str}' AND '{end_dt_str}'"""
