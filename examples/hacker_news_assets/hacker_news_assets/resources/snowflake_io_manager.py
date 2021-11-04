import os
import textwrap
from contextlib import contextmanager
from typing import Dict, Optional, Sequence, Union

from dagster import AssetKey, EventMetadataEntry, InputContext, OutputContext, check, io_manager
from dagster.core.storage.io_manager import IOManager
from pandas import DataFrame as PandasDataFrame
from pandas import read_sql
from pyspark.sql import DataFrame as SparkDataFrame
from pyspark.sql.types import StructField, StructType
from snowflake.connector.pandas_tools import pd_writer
from snowflake.sqlalchemy import URL  # pylint: disable=no-name-in-module,import-error
from sqlalchemy import create_engine

SHARED_SNOWFLAKE_CONF = {
    "account": os.getenv("SNOWFLAKE_ACCOUNT", ""),
    "user": os.getenv("SNOWFLAKE_USER", ""),
    "password": os.getenv("SNOWFLAKE_PASSWORD", ""),
    "database": "DEMO_DB",
    "warehouse": "TINY_WAREHOUSE",
}

DEV_SNOWFLAKE_CONF = dict(schema="hackernews_dev", **SHARED_SNOWFLAKE_CONF)
PROD_SNOWFLAKE_CONF = dict(schema="hackernews", **SHARED_SNOWFLAKE_CONF)


def spark_field_to_snowflake_type(spark_field: StructField):
    # Snowflake does not have a long type (all integer types have the same precision)
    spark_type = spark_field.dataType.typeName()
    if spark_type == "long":
        return "integer"
    else:
        return spark_type


@contextmanager
def connect_snowflake(config):
    url = URL(
        account=config["account"],
        user=config["user"],
        password=config["password"],
        database=config["database"],
        warehouse=config["warehouse"],
        schema=config["schema"],
        timezone="UTC",
    )

    conn = None
    try:
        conn = create_engine(url).connect()
        yield conn
    finally:
        if conn:
            conn.close()


@io_manager
def snowflake_io_manager_dev():
    return SnowflakeIOManager(config=DEV_SNOWFLAKE_CONF)


@io_manager
def snowflake_io_manager_prod():
    return SnowflakeIOManager(config=PROD_SNOWFLAKE_CONF)


@io_manager(required_resource_keys={"partition_start", "partition_end"})
def time_partitioned_snowflake_io_manager_prod():
    return TimePartitionedSnowflakeIOManager(config=PROD_SNOWFLAKE_CONF)


class SnowflakeIOManager(IOManager):
    """
    This IOManager can handle Outputs that are either pandas DataFrames or ParquetPointers (which
    are just paths that spark can interpret which store some parquet files). In either case, the
    data will be written to a Snowflake table specified by metadata on the relevant OutputDefinition.
    """

    def __init__(self, config):
        self.config = check.dict_param(config, "config")

    def handle_output(self, context: OutputContext, obj: Union[PandasDataFrame, SparkDataFrame]):
        schema, table = self.config["schema"], context.asset_key.path[-1]

        with connect_snowflake(config=self.config) as con:
            con.execute(self._get_cleanup_statement(table, context.resources))

        if isinstance(obj, SparkDataFrame):
            yield from self._handle_spark_output(self.config, obj, schema, table)
        elif isinstance(obj, PandasDataFrame):
            yield from self._handle_pandas_output(self.config, obj, table)
        elif obj is not None:
            raise Exception(
                "SnowflakeIOManager only supports pandas DataFrames and spark DataFrames"
            )

    def _handle_pandas_output(self, config: Dict, obj: PandasDataFrame, table: str):
        from snowflake import connector  # pylint: disable=no-name-in-module

        yield EventMetadataEntry.int(obj.shape[0], "Rows")
        yield EventMetadataEntry.md(pandas_columns_to_markdown(obj), "DataFrame columns")

        connector.paramstyle = "pyformat"
        with connect_snowflake(config=config) as con:
            with_uppercase_cols = obj.rename(str.upper, copy=False, axis="columns")
            with_uppercase_cols.to_sql(
                table, con=con, if_exists="replace", index=False, method=pd_writer,
            )

    def _handle_spark_output(self, config: Dict, df: SparkDataFrame, schema: str, table: str):
        options = {
            "sfURL": f"{config['account']}.snowflakecomputing.com",
            "sfUser": config["user"],
            "sfPassword": config["password"],
            "sfDatabase": config["database"],
            "sfSchema": schema,
            "sfWarehouse": config["warehouse"],
            "dbtable": table,
        }
        yield EventMetadataEntry.md(spark_columns_to_markdown(df.schema), "DataFrame columns")

        df.write.format("net.snowflake.spark.snowflake").options(**options).mode("append").save()

    def _get_cleanup_statement(self, table: str, _resources):
        return f"""
        DELETE FROM {table} WHERE true;
        """

    def _get_select_statement(
        self, _resources, asset_key: AssetKey, columns: Optional[Sequence[str]]
    ):
        col_str = ", ".join(f'"{c}"' for c in columns) if columns else "*"
        return f"""
        SELECT {col_str} FROM {asset_key.path[-1]};
        """

    def load_input(self, context: InputContext) -> PandasDataFrame:
        resources = context.resources
        with connect_snowflake(config=self.config) as con:
            result = read_sql(
                sql=self._get_select_statement(
                    resources, context.upstream_output.asset_key, context.metadata.get("columns")
                ),
                con=con,
            )
            result.columns = map(str.lower, result.columns)
            return result


class TimePartitionedSnowflakeIOManager(SnowflakeIOManager):
    """
    This version of the SnowflakeIOManager divides its data into seperate time partitions. Based on
    the values specified by the partition_start and partition_end resources, this will first delete
    the data that is present within those bounds, then load the output data into the table.

    This is useful for pipelines that run on a schedule, updating each hour (or day, etc.) with new
    data.
    """

    def get_output_asset_partitions(self, context: OutputContext):
        return [context.resources.partition_start]

    def _get_cleanup_statement(self, table: str, resources):
        return f"""
        DELETE FROM {table} WHERE
            TO_TIMESTAMP("time") BETWEEN
                '{resources.partition_start}' AND '{resources.partition_end}';
        """

    def _get_select_statement(
        self, resources, asset_key: AssetKey, columns: Optional[Sequence[str]],
    ):
        check.invariant(columns is None)
        return f"""
        SELECT * FROM {asset_key.path[-1]} WHERE
            TO_TIMESTAMP("time") BETWEEN
                '{resources.partition_start}' AND '{resources.partition_end}';
        """


def expectations_markdown():
    return textwrap.dedent(
        """
        - Column "story_id" was expected to be unique, but was not.
        - Unknown column "storie_id"
        """
    )


def pandas_columns_to_markdown(dataframe: PandasDataFrame) -> str:
    return (
        textwrap.dedent(
            """
        | Name | Type |
        | ---- | ---- |
    """
        )
        + "\n".join([f"| {name} | {dtype} |" for name, dtype in dataframe.dtypes.iteritems()])
    )


def spark_columns_to_markdown(schema: StructType) -> str:
    return (
        textwrap.dedent(
            """
        | Name | Type |
        | ---- | ---- |
    """
        )
        + "\n".join([f"| {field.name} | {field.dataType.typeName()} |" for field in schema.fields])
    )
