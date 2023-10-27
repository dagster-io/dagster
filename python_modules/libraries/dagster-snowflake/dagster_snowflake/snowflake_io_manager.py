from abc import abstractmethod
from contextlib import contextmanager
from typing import Optional, Sequence, Type, cast

from dagster import IOManagerDefinition, OutputContext, io_manager
from dagster._config.pythonic_config import (
    ConfigurableIOManagerFactory,
)
from dagster._core.definitions.time_window_partitions import TimeWindow
from dagster._core.storage.db_io_manager import (
    DbClient,
    DbIOManager,
    DbTypeHandler,
    TablePartitionDimension,
    TableSlice,
)
from dagster._core.storage.io_manager import dagster_maintained_io_manager
from pydantic import Field
from sqlalchemy.exc import ProgrammingError

from .resources import SnowflakeResource

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
                    "io_manager": snowflake_io_manager.configured({
                        "database": "my_database",
                        "account" : {"env": "SNOWFLAKE_ACCOUNT"}
                        ...
                    })
                }
            )

        If you do not provide a schema, Dagster will determine a schema based on the assets and ops using
        the IO Manager. For assets, the schema will be determined from the asset key,
        as shown in the above example. The final prefix before the asset name will be used as the schema. For example,
        if the asset ``my_table`` had the key prefix ``["snowflake", "my_schema"]``, the schema ``my_schema`` will be
        used. For ops, the schema can be specified by including a ``schema`` entry in output metadata. If ``schema`` is not provided
        via config or on the asset/op, ``public`` will be used for the schema.

        .. code-block:: python

            @op(
                out={"my_table": Out(metadata={"schema": "my_schema"})}
            )
            def make_my_table() -> pd.DataFrame:
                # the returned value will be stored at my_schema.my_table
                ...

        To only use specific columns of a table as input to a downstream op or asset, add the metadata ``columns`` to the
        In or AssetIn.

        .. code-block:: python

            @asset(
                ins={"my_table": AssetIn("my_table", metadata={"columns": ["a"]})}
            )
            def my_table_a(my_table: pd.DataFrame) -> pd.DataFrame:
                # my_table will just contain the data from column "a"
                ...

    """

    @dagster_maintained_io_manager
    @io_manager(config_schema=SnowflakeIOManager.to_config_schema())
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


class SnowflakeIOManager(ConfigurableIOManagerFactory):
    """Base class for an IO manager definition that reads inputs from and writes outputs to Snowflake.

    Examples:
        .. code-block:: python

            from dagster_snowflake import SnowflakeIOManager
            from dagster_snowflake_pandas import SnowflakePandasTypeHandler
            from dagster_snowflake_pyspark import SnowflakePySparkTypeHandler
            from dagster import Definitions, EnvVar

            class MySnowflakeIOManager(SnowflakeIOManager):
                @staticmethod
                def type_handlers() -> Sequence[DbTypeHandler]:
                    return [SnowflakePandasTypeHandler(), SnowflakePySparkTypeHandler()]

            @asset(
                key_prefix=["my_schema"]  # will be used as the schema in snowflake
            )
            def my_table() -> pd.DataFrame:  # the name of the asset will be the table name
                ...

            defs = Definitions(
                assets=[my_table],
                resources={
                    "io_manager": MySnowflakeIOManager(database="MY_DATABASE", account=EnvVar("SNOWFLAKE_ACCOUNT"), ...)
                }
            )

        If you do not provide a schema, Dagster will determine a schema based on the assets and ops using
        the IO Manager. For assets, the schema will be determined from the asset key,
        as shown in the above example. The final prefix before the asset name will be used as the schema. For example,
        if the asset ``my_table`` had the key prefix ``["snowflake", "my_schema"]``, the schema ``my_schema`` will be
        used. For ops, the schema can be specified by including a ``schema`` entry in output metadata. If ``schema`` is not provided
        via config or on the asset/op, ``public`` will be used for the schema.

        .. code-block:: python

            @op(
                out={"my_table": Out(metadata={"schema": "my_schema"})}
            )
            def make_my_table() -> pd.DataFrame:
                # the returned value will be stored at my_schema.my_table
                ...

        To only use specific columns of a table as input to a downstream op or asset, add the metadata ``columns`` to the
        In or AssetIn.

        .. code-block:: python

            @asset(
                ins={"my_table": AssetIn("my_table", metadata={"columns": ["a"]})}
            )
            def my_table_a(my_table: pd.DataFrame) -> pd.DataFrame:
                # my_table will just contain the data from column "a"
                ...

    """

    database: str = Field(description="Name of the database to use.")
    account: str = Field(
        description=(
            "Your Snowflake account name. For more details, see the `Snowflake documentation."
            " <https://docs.snowflake.com/developer-guide/python-connector/python-connector-api>`__"
        ),
    )
    user: str = Field(description="User login name.")
    schema_: Optional[str] = Field(
        default=None, alias="schema", description="Name of the schema to use."
    )  # schema is a reserved word for pydantic
    password: Optional[str] = Field(default=None, description="User password.")
    warehouse: Optional[str] = Field(default=None, description="Name of the warehouse to use.")
    role: Optional[str] = Field(default=None, description="Name of the role to use.")
    private_key: Optional[str] = Field(
        default=None,
        description=(
            "Raw private key to use. See the `Snowflake documentation"
            " <https://docs.snowflake.com/en/user-guide/key-pair-auth.html>`__ for details. To"
            " avoid issues with newlines in the keys, you can base64 encode the key. You can"
            " retrieve the base64 encoded key with this shell command: cat rsa_key.p8 | base64"
        ),
    )
    private_key_path: Optional[str] = Field(
        default=None,
        description=(
            "Path to the private key. See the `Snowflake documentation"
            " <https://docs.snowflake.com/en/user-guide/key-pair-auth.html>`__ for details."
        ),
    )
    private_key_password: Optional[str] = Field(
        default=None,
        description=(
            "The password of the private key. See the `Snowflake documentation"
            " <https://docs.snowflake.com/en/user-guide/key-pair-auth.html>`__ for details."
            " Required for both private_key and private_key_path if the private key is encrypted."
            " For unencrypted keys, this config can be omitted or set to None."
        ),
    )
    store_timestamps_as_strings: bool = Field(
        default=False,
        description=(
            "If using Pandas DataFrames, whether to convert time data to strings. If True, time"
            " data will be converted to strings when storing the DataFrame and converted back to"
            " time data when loading the DataFrame. If False, time data without a timezone will be"
            " set to UTC timezone to avoid a Snowflake bug. Defaults to False."
        ),
    )
    authenticator: Optional[str] = Field(
        default=None,
        description="Optional parameter to specify the authentication mechanism to use.",
    )

    @staticmethod
    @abstractmethod
    def type_handlers() -> Sequence[DbTypeHandler]:
        """type_handlers should return a list of the TypeHandlers that the I/O manager can use.

        .. code-block:: python

            from dagster_snowflake import SnowflakeIOManager
            from dagster_snowflake_pandas import SnowflakePandasTypeHandler
            from dagster_snowflake_pyspark import SnowflakePySparkTypeHandler
            from dagster import Definitions, EnvVar

            class MySnowflakeIOManager(SnowflakeIOManager):
                @staticmethod
                def type_handlers() -> Sequence[DbTypeHandler]:
                    return [SnowflakePandasTypeHandler(), SnowflakePySparkTypeHandler()]
        """
        ...

    @staticmethod
    def default_load_type() -> Optional[Type]:
        """If an asset or op is not annotated with an return type, default_load_type will be used to
        determine which TypeHandler to use to store and load the output.

        If left unimplemented, default_load_type will return None. In that case, if there is only
        one TypeHandler, the I/O manager will default to loading unannotated outputs with that
        TypeHandler.

        .. code-block:: python

            from dagster_snowflake import SnowflakeIOManager
            from dagster_snowflake_pandas import SnowflakePandasTypeHandler
            from dagster_snowflake_pyspark import SnowflakePySparkTypeHandler
            from dagster import Definitions, EnvVar
            import pandas as pd

            class MySnowflakeIOManager(SnowflakeIOManager):
                @staticmethod
                def type_handlers() -> Sequence[DbTypeHandler]:
                    return [SnowflakePandasTypeHandler(), SnowflakePySparkTypeHandler()]

                @staticmethod
                def default_load_type() -> Optional[Type]:
                    return pd.DataFrame
        """
        return None

    def create_io_manager(self, context) -> DbIOManager:
        return DbIOManager(
            db_client=SnowflakeDbClient(),
            io_manager_name="SnowflakeIOManager",
            database=self.database,
            schema=self.schema_,
            type_handlers=self.type_handlers(),
            default_load_type=self.default_load_type(),
        )


class SnowflakeDbClient(DbClient):
    @staticmethod
    @contextmanager
    def connect(context, table_slice):
        no_schema_config = (
            {k: v for k, v in context.resource_config.items() if k != "schema"}
            if context.resource_config
            else {}
        )
        with SnowflakeResource(
            schema=table_slice.schema, connector="sqlalchemy", **no_schema_config
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
    start_dt_str = start_dt.strftime(SNOWFLAKE_DATETIME_FORMAT)
    end_dt_str = end_dt.strftime(SNOWFLAKE_DATETIME_FORMAT)
    # Snowflake BETWEEN is inclusive; start <= partition expr <= end. We don't want to remove the next partition so we instead
    # write this as start <= partition expr < end.
    return f"""{table_partition.partition_expr} >= '{start_dt_str}' AND {table_partition.partition_expr} < '{end_dt_str}'"""


def _static_where_clause(table_partition: TablePartitionDimension) -> str:
    partitions = ", ".join(f"'{partition}'" for partition in table_partition.partitions)
    return f"""{table_partition.partition_expr} in ({partitions})"""
