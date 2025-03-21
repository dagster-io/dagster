from collections.abc import Mapping, Sequence
from typing import Optional

import dagster._check as check
from dagster import InputContext, MetadataValue, OutputContext, TableColumn, TableSchema
from dagster._core.definitions.metadata import RawMetadataValue
from dagster._core.storage.db_io_manager import DbTypeHandler, TableSlice
from dagster_snowflake import SnowflakeIOManager, build_snowflake_io_manager
from dagster_snowflake.snowflake_io_manager import SnowflakeDbClient
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.types import StructType

from dagster_snowflake_pyspark.constants import SNOWFLAKE_PARTNER_CONNECTION_IDENTIFIER_PYSPARK

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
        "APPLICATION": SNOWFLAKE_PARTNER_CONNECTION_IDENTIFIER_PYSPARK,
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

    def handle_output(  # pyright: ignore[reportIncompatibleMethodOverride]
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

    def load_input(self, context: InputContext, table_slice: TableSlice, _) -> DataFrame:  # pyright: ignore[reportIncompatibleMethodOverride]
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

    You can set a default schema to store the assets using the ``schema`` configuration value of the Snowflake I/O
    Manager. This schema will be used if no other schema is specified directly on an asset or op.

    .. code-block:: python

        defs = Definitions(
            assets=[my_table]
            resources={"io_manager" snowflake_pyspark_io_manager.configured(
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
        def my_table() -> DataFrame:
            ...

        @asset(
            metadata={"schema": "my_schema"}  # will be used as the schema in snowflake
        )
        def my_other_table() -> DataFrame:
            ...

    For ops, the schema can be specified by including a "schema" entry in output metadata.

    .. code-block:: python

        @op(
            out={"my_table": Out(metadata={"schema": "my_schema"})}
        )
        def make_my_table() -> DataFrame:
            ...

    If none of these is provided, the schema will default to "public".

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

        You can set a default schema to store the assets using the ``schema`` configuration value of the Snowflake I/O
        Manager. This schema will be used if no other schema is specified directly on an asset or op.

        .. code-block:: python

            defs = Definitions(
                assets=[my_table]
                resources={
                    "io_manager" SnowflakePySparkIOManager(database="my_database", schema="my_schema", ...)
                }
            )


        On individual assets, you an also specify the schema where they should be stored using metadata or
        by adding a ``key_prefix`` to the asset key. If both ``key_prefix`` and metadata are defined, the metadata will
        take precedence.

        .. code-block:: python

            @asset(
                key_prefix=["my_schema"]  # will be used as the schema in snowflake
            )
            def my_table() -> DataFrame:
                ...

            @asset(
                metadata={"schema": "my_schema"}  # will be used as the schema in snowflake
            )
            def my_other_table() -> DataFrame:
                ...

        For ops, the schema can be specified by including a "schema" entry in output metadata.

        .. code-block:: python

            @op(
                out={"my_table": Out(metadata={"schema": "my_schema"})}
            )
            def make_my_table() -> DataFrame:
                ...

        If none of these is provided, the schema will default to "public".
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
    def default_load_type() -> Optional[type]:
        return DataFrame
