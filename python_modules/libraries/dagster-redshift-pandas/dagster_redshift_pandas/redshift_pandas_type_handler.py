from contextlib import contextmanager
from typing import Mapping

import pandas as pd
from dagster import InputContext, MetadataValue, OutputContext, TableColumn, TableSchema
from dagster._core.definitions.metadata import RawMetadataValue
from dagster._core.storage.db_io_manager import DbTypeHandler, TableSlice
from dagster_aws.redshift import build_redshift_io_manager
from dagster_aws.redshift.io_manager import RedshiftDbClient


@contextmanager
def _connect_redshift_sqlalchemy(context, table_slice):
    from sqlalchemy import create_engine

    config = context.resource_config
    url = f"postgresql://{config['user']}:{config['password']}@{config['account']}.redshift.amazonaws.com:{config['port']}/{config['database']}/{table_slice.schema}"

    engine = create_engine(url)
    conn = engine.connect()

    yield conn

    conn.close()
    engine.dispose()


class RedshiftPandasTypeHandler(DbTypeHandler[pd.DataFrame]):
    """
    Plugin for the Redshift I/O Manager that can store and load Pandas DataFrames as Redshift tables.

    # TODO finish doc strings

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
        with _connect_redshift_sqlalchemy(context, table_slice) as conn:
            # TODO - create table if it doesn't exist

            with_uppercase_cols = obj.rename(str.upper, copy=False, axis="columns")
            with_uppercase_cols.to_sql(
                table_slice.table,
                con=conn.engine,
                if_exists="append",
                index=False,
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
        with _connect_redshift_sqlalchemy(context, table_slice) as conn:
            result = pd.read_sql(sql=RedshiftDbClient.get_select_statement(table_slice), con=conn)
            result.columns = map(str.lower, result.columns)
            return result

    @property
    def supported_types(self):
        return [pd.DataFrame]


redshift_pandas_io_manager = build_redshift_io_manager([RedshiftPandasTypeHandler()])
redshift_pandas_io_manager.__doc__ = """
An IO manager definition that reads inputs from and writes pandas dataframes to Redshift.

# TODO - finish doc string

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
