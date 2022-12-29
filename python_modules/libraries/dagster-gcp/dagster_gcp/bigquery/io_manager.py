from typing import Sequence

from google.cloud import bigquery

from dagster import Field, IOManagerDefinition, OutputContext, StringSource, io_manager
from dagster._core.storage.db_io_manager import (
    DbClient,
    DbIOManager,
    DbTypeHandler,
    TablePartition,
    TableSlice,
)

BIGQUERY_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


def build_bigquery_io_manager(type_handlers: Sequence[DbTypeHandler]) -> IOManagerDefinition:
    """
    Builds an IO manager definition that reads inputs from and writes outputs to BigQuery.

    # TODO - update doc string

    Args:
        type_handlers (Sequence[DbTypeHandler]): Each handler defines how to translate between
            DuckDB tables and an in-memory type - e.g. a Pandas DataFrame.

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

            @repository
            def my_repo():
                return with_resources(
                    [my_table],
                    {"io_manager": duckdb_io_manager.configured({"database": "my_db.duckdb"})}
                )

    If you do not provide a schema, Dagster will determine a schema based on the assets and ops using
    the IO Manager. For assets, the schema will be determined from the asset key. For ops, the schema can be
    specified by including a "schema" entry in output metadata. If none of these is provided, the schema will
    default to "public".

    .. code-block:: python

        @op(
            out={"my_table": Out(metadata={"schema": "my_schema"})}
        )
        def make_my_table() -> pd.DataFrame:
            ...

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

    @io_manager(
        config_schema={
            "dataset": Field(
                StringSource, description="Name of the schema to use.", is_required=False
            ),
            "project": Field(StringSource),  # elementl-dev - sort of like the database?
            "location": Field(StringSource, is_required=False),  # compute location? like us-east-2
        }
    )
    def bigquery_io_manager(init_context):
        """IO Manager for storing outputs in a BigQuery database

        # TODO update doc string

        Assets will be stored in the schema and table name specified by their AssetKey.
        Subsequent materializations of an asset will overwrite previous materializations of that asset.
        Op outputs will be stored in the schema specified by output metadata (defaults to public) in a
        table of the name of the output.
        """
        return DbIOManager(
            type_handlers=type_handlers,
            db_client=BigQueryClient(),
            io_manager_name="BigQueryIOManager",
            database=init_context.resource_config["project"],
            schema=init_context.resource_config.get("dataset"),
        )

    return bigquery_io_manager


class BigQueryClient(DbClient):
    @staticmethod
    def delete_table_slice(context: OutputContext, table_slice: TableSlice) -> None:
        print("IN DELETE")
        conn = _connect_bigquery(context)
        try:
            print("CKLEANUP STATEMENT")
            print(_get_cleanup_statement(table_slice))
            conn.query(_get_cleanup_statement(table_slice)).result()
            print("DONE DELETE")
        except Exception:  # TODO - find the real exception
            # table doesn't exist yet, so ignore the error
            pass
        # conn.close()

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


def _connect_bigquery(context):
    return bigquery.Client(
        project=context.resource_config.get("project"),
        location=context.resource_config.get("location"),
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
        return f"TRUNCATE TABLE {table_slice.database}.{table_slice.schema}.{table_slice.table}"


def _time_window_where_clause(table_partition: TablePartition) -> str:
    start_dt, end_dt = table_partition.time_window
    start_dt_str = start_dt.strftime(BIGQUERY_DATETIME_FORMAT)
    end_dt_str = end_dt.strftime(BIGQUERY_DATETIME_FORMAT)
    return f"""WHERE {table_partition.partition_expr} >= '{start_dt_str}' AND {table_partition.partition_expr} < '{end_dt_str}'"""
