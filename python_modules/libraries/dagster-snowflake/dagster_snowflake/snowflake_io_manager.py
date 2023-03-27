from contextlib import contextmanager
from typing import Mapping, Optional, Sequence, Type, cast

from dagster import Field, IOManagerDefinition, OutputContext, StringSource, io_manager
from dagster._core.definitions.time_window_partitions import TimeWindow
from dagster._core.storage.db_io_manager import (
    DbClient,
    DbIOManager,
    DbTypeHandler,
    TablePartitionDimension,
    TableSlice,
)
from sqlalchemy.exc import ProgrammingError

from .resources import SnowflakeConnection

SNOWFLAKE_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


def build_snowflake_io_manager(
    type_handlers: Sequence[DbTypeHandler], default_load_type: Optional[Type] = None
) -> IOManagerDefinition:
    """Builds an IO manager definition that reads inputs from and writes outputs to Snowflake.

    Args:
        type_handlers (Sequence[DbTypeHandler]): Each handler defines how to translate between
            slices of Snowflake tables and an in-memory type - e.g. a Pandas DataFrame. If only
            one DbTypeHandler is provided, it will be used as teh default_load_type.
        default_load_type (Type): When an input has no type annotation, load it as this type.

    Returns:
        IOManagerDefinition

    Examples:
        .. code-block:: python

            from dagster_snowflake import build_snowflake_io_manager
            from dagster_snowflake_pandas import SnowflakePandasTypeHandler
            from dagster_snowflake_pyspark import SnowflakePySparkTypeHandler
            from dagster import Definitions

            @asset(
                key_prefix=["my_schema"]  # will be used as the schema in snowflake
            )
            def my_table() -> pd.DataFrame:  # the name of the asset will be the table name
                ...

            snowflake_io_manager = build_snowflake_io_manager([SnowflakePandasTypeHandler(), SnowflakePySparkTypeHandler()])

            defs = Definitions(
                assets=[my_table],
                resources={
                    "io_manager": snowflake_pandas_io_manager.configured({
                        "database": "my_database",
                        "account" : {"env": "SNOWFLAKE_ACCOUNT"}
                        ...
                    })
                }
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
            default_load_type=default_load_type,
        )

    return snowflake_io_manager


class SnowflakeDbClient(DbClient):
    @staticmethod
    @contextmanager
    def connect(context, table_slice):
        no_schema_config = (
            {k: v for k, v in context.resource_config.items() if k != "schema"}
            if context.resource_config
            else {}
        )
        with SnowflakeConnection(
            dict(
                schema=table_slice.schema,
                connector="sqlalchemy",
                **cast(Mapping[str, str], no_schema_config),
            ),
            context.log,
        ).get_connection(raw_conn=False) as conn:
            yield conn

    @staticmethod
    def ensure_schema_exists(context: OutputContext, table_slice: TableSlice, connection) -> None:
        schemas = connection.execute(
            f"show schemas like '{table_slice.schema}' in database {table_slice.database}"
        ).fetchall()
        if len(schemas) == 0:
            connection.execute(f"create schema {table_slice.schema};")

    @staticmethod
    def delete_table_slice(context: OutputContext, table_slice: TableSlice, connection) -> None:
        try:
            connection.execute(_get_cleanup_statement(table_slice))
        except ProgrammingError:
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
            return query + _partition_where_clause(table_slice.partition_dimensions)
        else:
            return f"""SELECT {col_str} FROM {table_slice.database}.{table_slice.schema}.{table_slice.table}"""


def _get_cleanup_statement(table_slice: TableSlice) -> str:
    """Returns a SQL statement that deletes data in the given table to make way for the output data
    being written.
    """
    if table_slice.partition_dimensions and len(table_slice.partition_dimensions) > 0:
        query = (
            f"DELETE FROM {table_slice.database}.{table_slice.schema}.{table_slice.table} WHERE\n"
        )
        return query + _partition_where_clause(table_slice.partition_dimensions)
    else:
        return f"DELETE FROM {table_slice.database}.{table_slice.schema}.{table_slice.table}"


def _partition_where_clause(partition_dimensions: Sequence[TablePartitionDimension]) -> str:
    return " AND\n".join(
        _time_window_where_clause(partition_dimension)
        if isinstance(partition_dimension.partitions, TimeWindow)
        else _static_where_clause(partition_dimension)
        for partition_dimension in partition_dimensions
    )


def _time_window_where_clause(table_partition: TablePartitionDimension) -> str:
    partition = cast(TimeWindow, table_partition.partitions)
    start_dt, end_dt = partition
    start_dt_str = start_dt.strftime(SNOWFLAKE_DATETIME_FORMAT)
    end_dt_str = end_dt.strftime(SNOWFLAKE_DATETIME_FORMAT)
    # Snowflake BETWEEN is inclusive; start <= partition expr <= end. We don't want to remove the next partition so we instead
    # write this as start <= partition expr < end.
    return f"""{table_partition.partition_expr} >= '{start_dt_str}' AND {table_partition.partition_expr} < '{end_dt_str}'"""


def _static_where_clause(table_partition: TablePartitionDimension) -> str:
    partitions = ", ".join(f"'{partition}'" for partition in table_partition.partitions)
    return f"""{table_partition.partition_expr} in ({partitions})"""
