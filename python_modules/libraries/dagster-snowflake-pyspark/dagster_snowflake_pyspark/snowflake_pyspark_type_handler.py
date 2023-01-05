from typing import Mapping

from pyspark.sql import DataFrame
from pyspark.sql import SparkSession
from dagster_snowflake import build_snowflake_io_manager

from dagster import InputContext, MetadataValue, OutputContext, TableColumn, TableSchema
from dagster._core.definitions.metadata import RawMetadataValue
from dagster._core.storage.db_io_manager import DbTypeHandler, TableSlice


def _get_sf_options(config, table_slice):
    return {
        "sfURL": f"{config['account']}.snowflakecomputing.com",
        "sfUser": config["user"],
        "sfPassword": config["password"],
        "sfDatabase": config["database"],
        "sfSchema": table_slice.schema,
        "sfWarehouse": config["warehouse"],
        "dbtable": table_slice.table,
    }



class SnowflakePySparkTypeHandler(DbTypeHandler[DataFrame]):
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
        self, context: OutputContext, table_slice: TableSlice, obj: DataFrame
    ) -> Mapping[str, RawMetadataValue]:
        options = _get_sf_options(context.resource_config, table_slice)

        obj.write.format("net.snowflake.spark.snowflake").options(**options).mode("append").save()

        return {
            "row_count": obj.count(),
            "dataframe_columns": MetadataValue.table_schema(
                TableSchema(
                    columns=[
                        TableColumn(name=field.name, type=field.dataType.typeName())
                        for field in obj.schema.fields
                    ]
                )
            )
        }


    def load_input(self, context: InputContext, table_slice: TableSlice) -> DataFrame:
        options = _get_sf_options(context.resource_config, table_slice)

        spark = SparkSession.builder.getOrCreate()
        return spark.read.format("net.snowflake.spark.snowflake").options(**options).load()


    @property
    def supported_types(self):
        return [DataFrame]


snowflake_pyspark_io_manager = build_snowflake_io_manager([SnowflakePySparkTypeHandler()])
snowflake_pyspark_io_manager.__doc__ = """
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
