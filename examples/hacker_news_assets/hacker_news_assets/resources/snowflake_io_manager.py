import os
import textwrap
from contextlib import contextmanager
from typing import Optional, Sequence, Union

from dagster import AssetKey, EventMetadataEntry, InputContext, OutputContext, check, io_manager
from dagster.core.storage.io_manager import IOManager
from hacker_news_assets.resources.parquet_pointer import ParquetPointer
from pandas import DataFrame, read_sql
from pyspark.sql.types import StructField
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
        self.config = config

    def handle_output(self, context: OutputContext, obj: Union[ParquetPointer, DataFrame]):

        if isinstance(obj, ParquetPointer) and "s3:" in obj.path:
            yield from self._handle_pointer_output(context, obj)
        elif isinstance(obj, DataFrame):
            yield from self._handle_dataframe_output(context, obj)
        elif obj is not None:
            raise Exception(
                "SnowflakeIOManager only supports pandas DataFrames and s3 ParquetPointers"
            )

    def _handle_dataframe_output(self, context: OutputContext, obj: DataFrame):
        from snowflake import connector  # pylint: disable=no-name-in-module

        yield EventMetadataEntry.int(obj.shape[0], "Rows")
        yield EventMetadataEntry.md(columns_to_markdown(obj), "DataFrame columns")
        yield EventMetadataEntry.md(expectations_markdown(), "Failed expectations")

        connector.paramstyle = "pyformat"

        table = self.config["schema"], context.asset_key.path[-1]
        with connect_snowflake(config=self.config) as con:
            with_uppercase_cols = obj.rename(str.upper, copy=False, axis="columns")
            with_uppercase_cols.to_sql(
                table,
                con=con,
                if_exists="replace",
                index=False,
                method=pd_writer,
            )

    def _handle_pointer_output(self, context: OutputContext, parquet_pointer: ParquetPointer):

        yield EventMetadataEntry.path(parquet_pointer.path, "Source Parquet Path")
        with connect_snowflake(config=self.config) as con:
            # stage the data stored at the given path
            con.execute(
                f"""
            CREATE TEMPORARY STAGE tmp_s3_stage
                URL = '{parquet_pointer.path}'
                FILE_FORMAT=(TYPE=PARQUET COMPRESSION=SNAPPY)
                CREDENTIALS=(
                    AWS_KEY_ID='{os.getenv("AWS_ACCESS_KEY_ID")}',
                    AWS_SECRET_KEY='{os.getenv("AWS_SECRET_ACCESS_KEY")}'
                );
            """
            )
            con.execute(self._get_create_table_statement(context, parquet_pointer))
            con.execute(self._get_cleanup_statement(context))
            con.execute(self._get_copy_statement(context, parquet_pointer))

    def _get_create_table_statement(self, context: OutputContext, parquet_pointer: ParquetPointer):
        column_str = ",".join(
            f'"{field.name}" {spark_field_to_snowflake_type(field)}'
            for field in parquet_pointer.schema.fields
        )
        return f"""
        CREATE TABLE IF NOT EXISTS {context.asset_key.path[-1]} ({column_str});
        """

    def _get_copy_statement(self, context: OutputContext, parquet_pointer: ParquetPointer):
        # need to expand out the single parquet value into separate columns
        select_str = ",".join(f'$1:"{field.name}"' for field in parquet_pointer.schema.fields)
        return f"""
        COPY INTO {context.asset_key.path[-1]} FROM ( SELECT {select_str} FROM @tmp_s3_stage )
            PATTERN='.*parquet';
        """

    def _get_cleanup_statement(self, context: OutputContext):
        return f"""
        DELETE FROM {context.asset_key.path[-1]} WHERE true;
        """

    def _get_select_statement(
        self, _resources, asset_key: AssetKey, columns: Optional[Sequence[str]]
    ):
        col_str = ", ".join(f'"{c}"' for c in columns) if columns else "*"
        return f"""
        SELECT {col_str} FROM {asset_key.path[-1]};
        """

    def load_input(self, context: InputContext) -> DataFrame:
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

    def _get_cleanup_statement(self, context: OutputContext):
        return f"""
        DELETE FROM {context.asset_key.path[-1]} WHERE
            TO_TIMESTAMP("time") BETWEEN
                '{context.resources.partition_start}' AND '{context.resources.partition_end}';
        """

    def _get_select_statement(
        self,
        resources,
        asset_key: AssetKey,
        columns: Optional[Sequence[str]],
    ):
        check.invariant(columns is None)
        return f"""
        SELECT * FROM {asset_key.path[-1]} WHERE
            TO_TIMESTAMP("time") BETWEEN
                '{resources.partition_start}' AND '{resources.partition_end}';
        """


def columns_to_markdown(dataframe: DataFrame) -> str:
    return (
        textwrap.dedent(
            """
        | Name | Type |
        | ---- | ---- |
    """
        )
        + "\n".join([f"| {name} | {dtype}" for name, dtype in dataframe.dtypes.iteritems()])
    )


def expectations_markdown():
    return textwrap.dedent(
        """
        - Column "story_id" was expected to be unique, but was not.
        - Unknown column "storie_id"
        """
    )
