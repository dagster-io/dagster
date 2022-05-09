from typing import Mapping, Union, cast

from dagster_snowflake import DbTypeHandler
from dagster_snowflake.resources import SnowflakeConnection
from dagster_snowflake.snowflake_io_manager import SnowflakeDbClient, TableSlice
from pandas import DataFrame, read_sql
from snowflake.connector.pandas_tools import pd_writer

from dagster import InputContext, MetadataValue, OutputContext, TableColumn, TableSchema
from dagster.core.definitions.metadata import RawMetadataValue


def _connect_snowflake(context: Union[InputContext, OutputContext], table_slice: TableSlice):
    return SnowflakeConnection(
        dict(
            schema=table_slice.schema,
            connector="sqlalchemy",
            **cast(Mapping[str, str], context.resource_config),
        ),
        context.log,
    ).get_connection()


class SnowflakePandasTypeHandler(DbTypeHandler[DataFrame]):
    """
    Defines how to translate between slices of Snowflake tables and Pandas DataFrames.

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
        self, context: OutputContext, table_slice: TableSlice, obj: DataFrame
    ) -> Mapping[str, RawMetadataValue]:
        from snowflake import connector  # pylint: disable=no-name-in-module

        connector.paramstyle = "pyformat"
        with _connect_snowflake(context, table_slice) as con:
            with_uppercase_cols = obj.rename(str.upper, copy=False, axis="columns")
            with_uppercase_cols.to_sql(
                table_slice.table,
                con=con,
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

    def load_input(self, context: InputContext, table_slice: TableSlice) -> DataFrame:
        with _connect_snowflake(context, table_slice) as con:
            result = read_sql(sql=SnowflakeDbClient.get_select_statement(table_slice), con=con)
            result.columns = map(str.lower, result.columns)
            return result
