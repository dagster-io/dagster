from collections.abc import Mapping, Sequence
from typing import Optional

import numpy as np
import pandas as pd
from dagster import InputContext, MetadataValue, OutputContext, TableColumn, TableSchema
from dagster._core.definitions.metadata import RawMetadataValue, TableMetadataSet
from dagster._core.errors import DagsterInvariantViolationError
from dagster._core.storage.db_io_manager import DbTypeHandler, TableSlice
from dagster_snowflake import build_snowflake_io_manager
from dagster_snowflake.snowflake_io_manager import SnowflakeDbClient, SnowflakeIOManager
from snowflake.connector.pandas_tools import write_pandas


def _table_exists(table_slice: TableSlice, connection):
    tables = (
        connection.cursor()
        .execute(
            f"SHOW TABLES LIKE '{table_slice.table}' IN SCHEMA"
            f" {table_slice.database}.{table_slice.schema}"
        )
        .fetchall()
    )
    return len(tables) > 0


def _get_table_column_types(table_slice: TableSlice, connection) -> Optional[Mapping[str, str]]:
    if _table_exists(table_slice, connection):
        schema_list = connection.cursor().execute(f"DESCRIBE TABLE {table_slice.table}").fetchall()
        return {item[0]: item[1] for item in schema_list}


def _convert_timestamp_to_string(
    s: pd.Series, column_types: Optional[Mapping[str, str]], table_name: str
) -> pd.Series:
    """Converts columns of data of type pd.Timestamp to string so that it can be stored in
    snowflake.
    """
    column_name = str(s.name)
    if issubclass(s.dtype.type, (np.datetime64, np.timedelta64)):
        if column_types:
            if "VARCHAR" not in column_types[column_name]:
                raise DagsterInvariantViolationError(
                    "Snowflake I/O manager: Snowflake I/O manager configured to convert time data"
                    f" in DataFrame column {column_name} to strings, but the corresponding"
                    f" {column_name.upper()} column in table {table_name} is not of type VARCHAR,"
                    f" it is of type {column_types[column_name]}. Please set"
                    " store_timestamps_as_strings=False in the Snowflake I/O manager configuration"
                    " to store time data as TIMESTAMP types."
                )
        return s.dt.strftime("%Y-%m-%d %H:%M:%S.%f %z")
    else:
        return s


def _convert_string_to_timestamp(s: pd.Series) -> pd.Series:
    """Converts columns of strings in Timestamp format to pd.Timestamp to undo the conversion in
    _convert_timestamp_to_string.

    This will not convert non-timestamp strings into timestamps (pd.to_datetime will raise an
    exception if the string cannot be converted)
    """
    if isinstance(s[0], str):
        try:
            return pd.to_datetime(s.values)  # type: ignore  # (bad stubs)
        except ValueError:
            return s
    else:
        return s


class SnowflakePandasTypeHandler(DbTypeHandler[pd.DataFrame]):
    """Plugin for the Snowflake I/O Manager that can store and load Pandas DataFrames as Snowflake tables.

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
    """

    def handle_output(
        self, context: OutputContext, table_slice: TableSlice, obj: pd.DataFrame, connection
    ) -> Mapping[str, RawMetadataValue]:
        from snowflake import connector

        connector.paramstyle = "pyformat"
        with_uppercase_cols = obj.rename(str.upper, copy=False, axis="columns")
        column_types = _get_table_column_types(table_slice, connection)
        if context.resource_config and context.resource_config.get(
            "store_timestamps_as_strings", False
        ):
            with_uppercase_cols = with_uppercase_cols.apply(
                lambda x: _convert_timestamp_to_string(x, column_types, table_slice.table),
                axis="index",
            )

        write_pandas(
            conn=connection,
            df=with_uppercase_cols,
            # originally we used pd.to_sql with pd_writer method to write the df to snowflake. pd_writer
            # forced the database, schema, and table name to be uppercase, so we mimic that behavior here for feature parity
            # in the future we could allow non-uppercase names
            table_name=table_slice.table.upper(),
            schema=table_slice.schema.upper(),
            database=table_slice.database.upper() if table_slice.database else None,
            auto_create_table=True,
            use_logical_type=True,
            quote_identifiers=True,
        )

        return {
            # output object may be a slice/partition, so we output different metadata keys based on
            # whether this output represents an entire table or just a slice/partition
            **(
                TableMetadataSet(partition_row_count=obj.shape[0])
                if context.has_partition_key
                else TableMetadataSet(row_count=obj.shape[0])
            ),
            "dataframe_columns": MetadataValue.table_schema(
                TableSchema(
                    columns=[
                        TableColumn(name=str(name), type=str(dtype))
                        for name, dtype in obj.dtypes.items()
                    ]
                )
            ),
        }

    def load_input(
        self, context: InputContext, table_slice: TableSlice, connection
    ) -> pd.DataFrame:
        if table_slice.partition_dimensions and len(context.asset_partition_keys) == 0:
            return pd.DataFrame()
        result = pd.read_sql(
            sql=SnowflakeDbClient.get_select_statement(table_slice), con=connection
        )
        if context.resource_config and context.resource_config.get(
            "store_timestamps_as_strings", False
        ):
            result = result.apply(_convert_string_to_timestamp, axis="index")
        result.columns = map(str.lower, result.columns)  # type: ignore  # (bad stubs)
        return result

    @property
    def supported_types(self):
        return [pd.DataFrame]


snowflake_pandas_io_manager = build_snowflake_io_manager(
    [SnowflakePandasTypeHandler()], default_load_type=pd.DataFrame
)
snowflake_pandas_io_manager.__doc__ = """
An I/O manager definition that reads inputs from and writes Pandas DataFrames to Snowflake. When
using the snowflake_pandas_io_manager, any inputs and outputs without type annotations will be loaded
as Pandas DataFrames.


Returns:
    IOManagerDefinition

Examples:

    .. code-block:: python

        from dagster_snowflake_pandas import snowflake_pandas_io_manager
        from dagster import asset, Definitions

        @asset(
            key_prefix=["my_schema"]  # will be used as the schema in snowflake
        )
        def my_table() -> pd.DataFrame:  # the name of the asset will be the table name
            ...

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

    You can set a default schema to store the assets using the ``schema`` configuration value of the Snowflake I/O
    Manager. This schema will be used if no other schema is specified directly on an asset or op.

    .. code-block:: python

        defs = Definitions(
            assets=[my_table]
            resources={"io_manager" snowflake_pandas_io_manager.configured(
                {"database": "my_database", "schema": "my_schema", ...} # will be used as the schema
            )}
        )


    On individual assets, you an also specify the schema where they should be stored using metadata or
    by adding a ``key_prefix`` to the asset key. If both ``key_prefix`` and metadata are defined, the metadata will
    take precedence.

    .. code-block:: python

        @asset(
            key_prefix=["my_schema"]  # will be used as the schema in snowflake
        )
        def my_table() -> pd.DataFrame:
            ...

        @asset(
            metadata={"schema": "my_schema"}  # will be used as the schema in snowflake
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
        def my_table_a(my_table: pd.DataFrame) -> pd.DataFrame:
            # my_table will just contain the data from column "a"
            ...

"""


class SnowflakePandasIOManager(SnowflakeIOManager):
    """An I/O manager definition that reads inputs from and writes Pandas DataFrames to Snowflake. When
    using the SnowflakePandasIOManager, any inputs and outputs without type annotations will be loaded
    as Pandas DataFrames.


    Returns:
        IOManagerDefinition

    Examples:
        .. code-block:: python

            from dagster_snowflake_pandas import SnowflakePandasIOManager
            from dagster import asset, Definitions, EnvVar

            @asset(
                key_prefix=["my_schema"]  # will be used as the schema in snowflake
            )
            def my_table() -> pd.DataFrame:  # the name of the asset will be the table name
                ...

            defs = Definitions(
                assets=[my_table],
                resources={
                    "io_manager": SnowflakePandasIOManager(database="MY_DATABASE", account=EnvVar("SNOWFLAKE_ACCOUNT"), ...)
                }
            )

        You can set a default schema to store the assets using the ``schema`` configuration value of the Snowflake I/O
        Manager. This schema will be used if no other schema is specified directly on an asset or op.

        .. code-block:: python

            defs = Definitions(
                assets=[my_table]
                resources={
                    "io_manager" SnowflakePandasIOManager(database="my_database", schema="my_schema", ...)
                }
            )


        On individual assets, you an also specify the schema where they should be stored using metadata or
        by adding a ``key_prefix`` to the asset key. If both ``key_prefix`` and metadata are defined, the metadata will
        take precedence.

        .. code-block:: python

            @asset(
                key_prefix=["my_schema"]  # will be used as the schema in snowflake
            )
            def my_table() -> pd.DataFrame:
                ...

            @asset(
                metadata={"schema": "my_schema"}  # will be used as the schema in snowflake
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
            def my_table_a(my_table: pd.DataFrame) -> pd.DataFrame:
                # my_table will just contain the data from column "a"
                ...

    """

    @classmethod
    def _is_dagster_maintained(cls) -> bool:
        return True

    @staticmethod
    def type_handlers() -> Sequence[DbTypeHandler]:
        return [SnowflakePandasTypeHandler()]

    @staticmethod
    def default_load_type() -> Optional[type]:
        return pd.DataFrame
