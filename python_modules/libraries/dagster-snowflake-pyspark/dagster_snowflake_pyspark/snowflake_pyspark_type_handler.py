from typing import Mapping, Optional, Sequence, Type

import dagster._check as check
from dagster import InputContext, MetadataValue, OutputContext, TableColumn, TableSchema
from dagster._core.definitions.metadata import RawMetadataValue
from dagster._core.storage.db_io_manager import DbTypeHandler, TableSlice
from dagster_snowflake import SnowflakeIOManager, build_snowflake_io_manager
from dagster_snowflake.snowflake_io_manager import SnowflakeDbClient
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.types import StructType

SNOWFLAKE_CONNECTOR = "net.snowflake.spark.snowflake"


def _get_snowflake_options(config, table_slice: TableSlice) -> Mapping[str, str]:
    check.invariant(
        config.get("warehouse", None) is not None,
        "Missing config: Warehouse is required when using PySpark with the Snowflake I/O manager.",
    )

    conf = {
        "sfURL": f"{config['account']}.snowflakecomputing.com",
        "sfUser": config["user"],
        "sfPassword": config["password"],
        "sfDatabase": config["database"],
        "sfSchema": table_slice.schema,
        "sfWarehouse": config["warehouse"],
    }

    return conf


class SnowflakePySparkTypeHandler(DbTypeHandler[DataFrame]):
    """Plugin for the Snowflake I/O Manager that can store and load PySpark DataFrames as Snowflake tables.

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
                    "io_manager": MySnowflakeIOManager(database="MY_DATABASE", account=EnvVar("SNOWFLAKE_ACCOUNT"), warehouse="my_warehouse", ...)
                }
            )

    """

    def handle_output(
        self, context: OutputContext, table_slice: TableSlice, obj: DataFrame, _
    ) -> Mapping[str, RawMetadataValue]:
        options = _get_snowflake_options(context.resource_config, table_slice)

        with_uppercase_cols = obj.toDF(*[c.upper() for c in obj.columns])

        with_uppercase_cols.write.format(SNOWFLAKE_CONNECTOR).options(**options).option(
            "dbtable", table_slice.table
        ).mode("append").save()

        return {
            "dataframe_columns": MetadataValue.table_schema(
                TableSchema(
                    columns=[
                        TableColumn(name=field.name, type=field.dataType.typeName())
                        for field in obj.schema.fields
                    ]
                )
            ),
        }

    def load_input(self, context: InputContext, table_slice: TableSlice, _) -> DataFrame:
        options = _get_snowflake_options(context.resource_config, table_slice)

        spark = SparkSession.builder.getOrCreate()  # type: ignore
        if table_slice.partition_dimensions and len(context.asset_partition_keys) == 0:
            return spark.createDataFrame([], StructType([]))

        df = (
            spark.read.format(SNOWFLAKE_CONNECTOR)
            .options(**options)
            .option("query", SnowflakeDbClient.get_select_statement(table_slice))
            .load()
        )
        return df.toDF(*[c.lower() for c in df.columns])

    @property
    def supported_types(self):
        return [DataFrame]


snowflake_pyspark_io_manager = build_snowflake_io_manager(
    [SnowflakePySparkTypeHandler()], default_load_type=DataFrame
)
snowflake_pyspark_io_manager.__doc__ = """
An I/O manager definition that reads inputs from and writes PySpark DataFrames to Snowflake. When
using the snowflake_pyspark_io_manager, any inputs and outputs without type annotations will be loaded
as PySpark DataFrames.

Returns:
    IOManagerDefinition

Examples:

    .. code-block:: python

        from dagster_snowflake_pyspark import snowflake_pyspark_io_manager
        from pyspark.sql import DataFrame
        from dagster import Definitions

        @asset(
            key_prefix=["my_schema"]  # will be used as the schema in snowflake
        )
        def my_table() -> DataFrame:  # the name of the asset will be the table name
            ...

        defs = Definitions(
            assets=[my_table],
            resources={
                "io_manager": snowflake_pyspark_io_manager.configured({
                    "database": "my_database",
                    "warehouse": "my_warehouse", # required for snowflake_pyspark_io_manager
                    "account" : {"env": "SNOWFLAKE_ACCOUNT"},
                    "password": {"env": "SNOWFLAKE_PASSWORD"},
                    ...
                })
            }
        )

    Note that the warehouse configuration value is required when using the snowflake_pyspark_io_manager

    If you do not provide a schema, Dagster will determine a schema based on the assets and ops using
    the I/O Manager. For assets, the schema will be determined from the asset key.
    For ops, the schema can be specified by including a "schema" entry in output metadata. If "schema" is not provided
    via config or on the asset/op, "public" will be used for the schema.

    .. code-block:: python

        @op(
            out={"my_table": Out(metadata={"schema": "my_schema"})}
        )
        def make_my_table() -> DataFrame:
            # the returned value will be stored at my_schema.my_table
            ...

    To only use specific columns of a table as input to a downstream op or asset, add the metadata "columns" to the
    In or AssetIn.

    .. code-block:: python

        @asset(
            ins={"my_table": AssetIn("my_table", metadata={"columns": ["a"]})}
        )
        def my_table_a(my_table: DataFrame) -> DataFrame:
            # my_table will just contain the data from column "a"
            ...

"""


class SnowflakePySparkIOManager(SnowflakeIOManager):
    """An I/O manager definition that reads inputs from and writes PySpark DataFrames to Snowflake. When
    using the SnowflakePySparkIOManager, any inputs and outputs without type annotations will be loaded
    as PySpark DataFrames.

    Returns:
        IOManagerDefinition

    Examples:
        .. code-block:: python

            from dagster_snowflake_pyspark import SnowflakePySparkIOManager
            from pyspark.sql import DataFrame
            from dagster import Definitions, EnvVar

            @asset(
                key_prefix=["my_schema"]  # will be used as the schema in snowflake
            )
            def my_table() -> DataFrame:  # the name of the asset will be the table name
                ...

            defs = Definitions(
                assets=[my_table],
                resources={
                    "io_manager": SnowflakePySparkIOManager(
                        database="my_database",
                        warehouse="my_warehouse", # required for SnowflakePySparkIOManager
                        account=EnvVar("SNOWFLAKE_ACCOUNT"),
                        password=EnvVar("SNOWFLAKE_PASSWORD"),
                        ...
                    )
                }
            )

        Note that the warehouse configuration value is required when using the SnowflakePySparkIOManager

        If you do not provide a schema, Dagster will determine a schema based on the assets and ops using
        the I/O Manager. For assets, the schema will be determined from the asset key, as in the above example.
        For ops, the schema can be specified by including a "schema" entry in output metadata. If "schema" is not provided
        via config or on the asset/op, "public" will be used for the schema.

        .. code-block:: python

            @op(
                out={"my_table": Out(metadata={"schema": "my_schema"})}
            )
            def make_my_table() -> DataFrame:
                # the returned value will be stored at my_schema.my_table
                ...

        To only use specific columns of a table as input to a downstream op or asset, add the metadata "columns" to the
        In or AssetIn.

        .. code-block:: python

            @asset(
                ins={"my_table": AssetIn("my_table", metadata={"columns": ["a"]})}
            )
            def my_table_a(my_table: DataFrame) -> DataFrame:
                # my_table will just contain the data from column "a"
                ...

    """

    @classmethod
    def _is_dagster_maintained(cls) -> bool:
        return True

    @staticmethod
    def type_handlers() -> Sequence[DbTypeHandler]:
        return [SnowflakePySparkTypeHandler()]

    @staticmethod
    def default_load_type() -> Optional[Type]:
        return DataFrame
