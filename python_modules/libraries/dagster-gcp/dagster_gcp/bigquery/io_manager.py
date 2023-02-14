import os
import tempfile
from typing import Sequence, cast

from dagster import Field, IOManagerDefinition, Noneable, OutputContext, StringSource, io_manager
from dagster._core.storage.db_io_manager import (
    DbClient,
    DbIOManager,
    DbTypeHandler,
    TablePartitionDimension,
    TableSlice,
    TimeWindow,
)
from google.cloud import bigquery

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
                StringSource, description="Name of the BigQuery dataset to use.", is_required=False
            ),
            "project": Field(
                StringSource, description="The GCP project to use."
            ),  # elementl-dev - sort of like the database?
            "location": Field(
                Noneable(StringSource),
                is_required=False,
                default_value=None,
                description="The GCP location.",
            ),  # compute location? like us-east-2
            "gcp_credentials": Field(
                Noneable(StringSource),
                is_required=False,
                default_value=None,
                description=(
                    "GCP authentication credentials. If provided, a temporary file will be created"
                    " with the credentials and GOOGLE_APPLICATION_CREDENTIALS will be set to the"
                    " temporary file."
                ),
            ),
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
        temp_file_name = ""
        if init_context.resource_config.get("gcp_credentials"):
            with tempfile.NamedTemporaryFile("w", delete=False) as f:
                f.write(init_context.resource_config.get("gcp_credentials"))
                temp_file_name = f.name
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = temp_file_name

        yield DbIOManager(
            type_handlers=type_handlers,
            db_client=BigQueryClient(),
            io_manager_name="BigQueryIOManager",
            database=init_context.resource_config["project"],
            schema=init_context.resource_config.get("dataset"),
        )
        if init_context.resource_config.get("gcp_credentials"):
            os.environ.pop("GOOGLE_APPLICATION_CREDENTIALS", None)
            os.remove(temp_file_name)

    return bigquery_io_manager


class BigQueryClient(DbClient):
    @staticmethod
    def delete_table_slice(context: OutputContext, table_slice: TableSlice) -> None:
        conn = _connect_bigquery(context)
        try:
            conn.query(_get_cleanup_statement(table_slice)).result()
        except Exception:  # TODO - find the real exception
            # table doesn't exist yet, so ignore the error
            pass

    @staticmethod
    def get_select_statement(table_slice: TableSlice) -> str:
        col_str = ", ".join(table_slice.columns) if table_slice.columns else "*"

        if table_slice.partition_dimensions and len(table_slice.partition_dimensions) > 0:
            query = (
                f"SELECT {col_str} FROM"
                f" {table_slice.database}.{table_slice.schema}.{table_slice.table} WHERE\n"
            )
            partition_where = " AND\n".join(
                _static_where_clause(partition_dimension)
                if isinstance(partition_dimension.partition, str)
                else _time_window_where_clause(partition_dimension)
                for partition_dimension in table_slice.partition_dimensions
            )
            return query + partition_where
        else:
            return f"""SELECT {col_str} FROM {table_slice.database}.{table_slice.schema}.{table_slice.table}"""

    @staticmethod
    def ensure_schema_exists(context: OutputContext, table_slice: TableSlice) -> None:
        bq_client = _connect_bigquery(context)
        bq_client.query(f"CREATE SCHEMA IF NOT EXISTS {table_slice.schema}").result()


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
    if table_slice.partition_dimensions and len(table_slice.partition_dimensions) > 0:
        query = (
            f"DELETE FROM {table_slice.database}.{table_slice.schema}.{table_slice.table} WHERE\n"
        )

        partition_where = " AND\n".join(
            _static_where_clause(partition_dimension)
            if isinstance(partition_dimension.partition, str)
            else _time_window_where_clause(partition_dimension)
            for partition_dimension in table_slice.partition_dimensions
        )
        return query + partition_where
    else:
        return f"TRUNCATE TABLE {table_slice.database}.{table_slice.schema}.{table_slice.table}"


def _time_window_where_clause(table_partition: TablePartitionDimension) -> str:
    partition = cast(TimeWindow, table_partition.partition)
    start_dt, end_dt = partition
    start_dt_str = start_dt.strftime(BIGQUERY_DATETIME_FORMAT)
    end_dt_str = end_dt.strftime(BIGQUERY_DATETIME_FORMAT)
    return f"""{table_partition.partition_expr} >= '{start_dt_str}' AND {table_partition.partition_expr} < '{end_dt_str}'"""


def _static_where_clause(table_partition: TablePartitionDimension) -> str:
    return f"""{table_partition.partition_expr} = '{table_partition.partition}'"""
