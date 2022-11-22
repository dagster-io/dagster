from typing import Mapping, Union, cast

import pandas as pd
from dagster_snowflake import build_snowflake_io_manager
from dagster_snowflake.resources import SnowflakeConnection
from dagster_snowflake.snowflake_io_manager import SnowflakeDbClient
from snowflake.connector.pandas_tools import pd_writer

from dagster import (
    IOManagerDefinition,
    InputContext,
    MetadataValue,
    OutputContext,
    TableColumn,
    TableSchema,
)
from dagster._core.definitions.metadata import RawMetadataValue
from dagster._core.storage.db_io_manager import DbTypeHandler, TableSlice


def _connect_snowflake(context: Union[InputContext, OutputContext], table_slice: TableSlice):
    no_schema_config = (
        {k: v for k, v in context.resource_config.items() if k != "schema"}
        if context.resource_config
        else {}
    )
    return SnowflakeConnection(
        dict(
            schema=table_slice.schema,
            connector="sqlalchemy",
            **cast(Mapping[str, str], no_schema_config),
        ),
        context.log,
    ).get_connection(raw_conn=False)


def _convert_timestamp_to_string(s: pd.Series) -> pd.Series:
    """
    Converts columns of data of type pd.Timestamp to string so that it can be stored in
    snowflake
    """
    if pd.core.dtypes.common.is_datetime_or_timedelta_dtype(s):
        return s.dt.strftime("%Y-%m-%d %H:%M:%S.%f %z")
    else:
        return s


def _convert_string_to_timestamp(s: pd.Series) -> pd.Series:
    """
    Converts columns of strings in Timestamp format to pd.Timestamp to undo the conversion in
    _convert_timestamp_to_string

    This will not convert non-timestamp strings into timestamps (pd.to_datetime will raise an
    exception if the string cannot be converted)
    """
    if isinstance(s[0], str):
        try:
            return pd.to_datetime(s.values)
        except ValueError:
            return s
    else:
        return s


class SnowflakePandasTypeHandler(DbTypeHandler[pd.DataFrame]):
    """
    Plugin for the Snowflake I/O Manager that can store and load Pandas DataFrames as Snowflake tables.

    Examples:

    .. code-block:: python

        from dagster_snowflake import build_snowflake_io_manager
        from dagster_snowflake_pandas import SnowflakePandasTypeHandler

        snowflake_io_manager = build_snowflake_io_manager([SnowflakePandasTypeHandler()])

        @job(resource_defs={'io_manager': snowflake_io_manager})
        def my_job():
            ...
    """

    def handle_output(
        self, context: OutputContext, table_slice: TableSlice, obj: pd.DataFrame
    ) -> Mapping[str, RawMetadataValue]:
        from snowflake import connector  # pylint: disable=no-name-in-module

        connector.paramstyle = "pyformat"
        with _connect_snowflake(context, table_slice) as con:
            with_uppercase_cols = obj.rename(str.upper, copy=False, axis="columns")
            with_uppercase_cols = with_uppercase_cols.apply(
                _convert_timestamp_to_string, axis="index"
            )
            with_uppercase_cols.to_sql(
                table_slice.table,
                con=con.engine,
                if_exists="append",
                index=False,
                method=pd_writer,
            )

        return {
            "row_count": obj.shape[0],
            "dataframe_columns": MetadataValue.table_schema(
                TableSchema(
                    columns=[
                        TableColumn(name=name, type=str(dtype))
                        for name, dtype in obj.dtypes.iteritems()
                    ]
                )
            ),
        }

    def load_input(self, context: InputContext, table_slice: TableSlice) -> pd.DataFrame:
        with _connect_snowflake(context, table_slice) as con:
            result = pd.read_sql(sql=SnowflakeDbClient.get_select_statement(table_slice), con=con)
            result = result.apply(_convert_string_to_timestamp, axis="index")
            result.columns = map(str.lower, result.columns)
            return result

    @property
    def supported_types(self):
        return [pd.DataFrame]


# Helper function used as a decorator below
# The only purpose in doing this is so that
# we have a symbol to hang the snowflake_pandas_io_manager
# docblock off of. Otherwise we would just invoke build_snowflake_io_manager
# directly and assign to module-scoped variable
def wrap_io_manager(fn) -> IOManagerDefinition:
    return fn()


@wrap_io_manager
def snowflake_pandas_io_manager():
    """
    An IO manager definition that reads inputs from and writes pandas dataframes to Snowflake.

    Returns:
        IOManagerDefinition

    Examples:

        .. code-block:: python

            from dagster_snowflake_pandas import snowflake_pandas_io_manager

            @asset(
                key_prefix=["my_schema"]  # will be used as the schema in snowflake
            )
            def my_table() -> pd.DataFrame:  # the name of the asset will be the table name
                ...

            @repository
            def my_repo():
                return with_resources(
                    [my_table],
                    {"io_manager": snowflake_pandas_io_manager.configured({
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
    return build_snowflake_io_manager([SnowflakePandasTypeHandler()])
