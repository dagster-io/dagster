from typing import Sequence

from dagster import Field, IOManagerDefinition, OutputContext, StringSource, io_manager
from dagster._core.storage.db_io_manager import (
    DbClient,
    DbIOManager,
    DbTypeHandler,
    TablePartition,
    TableSlice,
)
from snowflake.connector import ProgrammingError

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

            @asset(
                key_prefix=["my_schema"]  # will be used as the schema in snowflake
            )
            def my_table() -> pd.DataFrame:  # the name of the asset will be the table name
                ...

            snowflake_io_manager = build_snowflake_io_manager([SnowflakePandasTypeHandler()])
            @repository
            def my_repo():
                return with_resources(
                    [my_table],
                    {"io_manager": snowflake_io_manager.configured({
                        "database": "my_database",
                        "account" : {"env": "SNOWFLAKE_ACCOUNT"}
                        ...
                    })}
                )

        If you do not provide a schema, Dagster will determine a schema based on the assets and ops using
        the IO Manager. For assets, the schema will be determined from the asset key.
        For ops, the schema can be specified by including a "schema" entry in output metadata. If "schema" is not provided
        via config or on the asset/op, "public" will be used for the schema.

        .. code-block:: python

            @op(
                out={"my_table": Out(metadata={"schema": "my_schema"})}
            )
            def make_my_table() -> pd.DataFrame:
                # the returned value will be stored at my_schema.my_table
                ...

        To only use specific columns of a table as input to a downstream op or asset, add the metadata "columns" to the
        In or AssetIn.

        .. code-block:: python

            @asset(
                ins={"my_table": AssetIn("my_table", metadata={"columns": ["a"]})}
            )
            def my_table_a(my_table: pd.DataFrame) -> pd.DataFrame:
                # my_table will just contain the data from column "a"
                ...

    """

    @io_manager(
        config_schema={
            "database": Field(StringSource, description="Name of the database to use."),
            "account": Field(
                StringSource,
                description=(
                    "Your Snowflake account name. For more details, see  https://bit.ly/2FBL320."
                ),
            ),
            "user": Field(StringSource, description="User login name."),
            "password": Field(StringSource, description="User password.", is_required=False),
            "warehouse": Field(
                StringSource, description="Name of the warehouse to use.", is_required=False
            ),
            "schema": Field(
                StringSource, description="Name of the schema to use.", is_required=False
            ),
            "role": Field(StringSource, description="Name of the role to use.", is_required=False),
            "private_key": Field(
                StringSource,
                description=(
                    "Raw private key to use. See"
                    " https://docs.snowflake.com/en/user-guide/key-pair-auth.html for details."
                ),
                is_required=False,
            ),
            "private_key_path": Field(
                StringSource,
                description=(
                    "Path to the private key. See"
                    " https://docs.snowflake.com/en/user-guide/key-pair-auth.html for details."
                ),
                is_required=False,
            ),
            "private_key_password": Field(
                StringSource,
                description=(
                    "The password of the private key. See"
                    " https://docs.snowflake.com/en/user-guide/key-pair-auth.html for details."
                ),
                is_required=False,
            ),
        }
    )
    def snowflake_io_manager(init_context):
        return DbIOManager(
            type_handlers=type_handlers,
            db_client=SnowflakeDbClient(),
            io_manager_name="SnowflakeIOManager",
            database=init_context.resource_config["database"],
            schema=init_context.resource_config.get("schema"),
        )

    return snowflake_io_manager


class SnowflakeDbClient(DbClient):
    @staticmethod
    def delete_table_slice(context: OutputContext, table_slice: TableSlice) -> None:
        no_schema_config = (
            {k: v for k, v in context.resource_config.items() if k != "schema"}
            if context.resource_config
            else {}
        )
        with SnowflakeConnection(
            dict(schema=table_slice.schema, **no_schema_config), context.log  # type: ignore
        ).get_connection() as con:
            try:
                con.execute_string(_get_cleanup_statement(table_slice))
            except ProgrammingError:
                # table doesn't exist yet, so ignore the error
                pass

    @staticmethod
    def get_select_statement(table_slice: TableSlice) -> str:
        col_str = ", ".join(table_slice.columns) if table_slice.columns else "*"
        if table_slice.partition:
            return (
                f"SELECT {col_str} FROM"
                f" {table_slice.database}.{table_slice.schema}.{table_slice.table}\n"
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
    # Snowflake BETWEEN is inclusive; start <= partition expr <= end. We don't want to remove the next partition so we instead
    # write this as start <= partition expr < end.
    return f"""WHERE {table_partition.partition_expr} >= '{start_dt_str}' AND {table_partition.partition_expr} < '{end_dt_str}'"""
