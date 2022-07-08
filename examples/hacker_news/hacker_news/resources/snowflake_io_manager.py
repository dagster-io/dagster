import os
import textwrap
from contextlib import contextmanager
from typing import Any, Mapping, Optional, Sequence, Union, cast

from pandas import DataFrame as PandasDataFrame
from pandas import read_sql
from pyspark.sql import DataFrame as SparkDataFrame
from pyspark.sql.types import StructField, StructType
from snowflake.connector.pandas_tools import pd_writer
from snowflake.sqlalchemy import URL  # pylint: disable=no-name-in-module,import-error
from sqlalchemy import create_engine

import dagster._check as check
from dagster import AssetKey, IOManager, InputContext, MetadataEntry, OutputContext, io_manager


def spark_field_to_snowflake_type(spark_field: StructField):
    # Snowflake does not have a long type (all integer types have the same precision)
    spark_type = spark_field.dataType.typeName()
    if spark_type == "long":
        return "integer"
    else:
        return spark_type


SHARED_SNOWFLAKE_CONF = {
    "account": os.getenv("SNOWFLAKE_ACCOUNT", ""),
    "user": os.getenv("SNOWFLAKE_USER", ""),
    "password": os.getenv("SNOWFLAKE_PASSWORD", ""),
    "warehouse": "TINY_WAREHOUSE",
}


@contextmanager
def connect_snowflake(config, schema="public"):
    url = URL(
        account=config["account"],
        user=config["user"],
        password=config["password"],
        database=config["database"],
        warehouse=config["warehouse"],
        schema=schema,
        timezone="UTC",
    )

    conn = None
    try:
        conn = create_engine(url).connect()
        yield conn
    finally:
        if conn:
            conn.close()


@io_manager(config_schema={"database": str}, required_resource_keys={"partition_bounds"})
def snowflake_io_manager(init_context):
    return SnowflakeIOManager(
        config=dict(database=init_context.resource_config["database"], **SHARED_SNOWFLAKE_CONF)
    )


class SnowflakeIOManager(IOManager):
    """
    This IOManager can handle outputs that are either Spark or Pandas DataFrames. In either case,
    the data will be written to a Snowflake table specified by metadata on the relevant Out.

    If an Out has {"partitioned": True} in its metadata, we just overwrite a single partition, based
    on the time window specified by the partition_bounds resource.

    Because we specify a get_output_asset_key() function, AssetMaterialization events will be
    automatically created each time an output is processed with this IOManager.
    """

    def __init__(self, config):
        self._config = config

    def handle_output(self, context: OutputContext, obj: Union[PandasDataFrame, SparkDataFrame]):
        metadata = check.not_none(context.metadata)
        schema, table = cast(str, metadata["table"]).split(".")

        partition_bounds = (
            context.resources.partition_bounds if metadata.get("partitioned") is True else None
        )
        with connect_snowflake(config=self._config, schema=schema) as con:
            con.execute(self._get_cleanup_statement(table, schema, partition_bounds))

        if isinstance(obj, SparkDataFrame):
            yield from self._handle_spark_output(obj, schema, table)
        elif isinstance(obj, PandasDataFrame):
            yield from self._handle_pandas_output(obj, schema, table)
        else:
            raise Exception(
                "SnowflakeIOManager only supports pandas DataFrames and spark DataFrames"
            )

        columns = cast(Optional[Sequence[str]], metadata.get("columns"))
        yield MetadataEntry.text(
            self._get_select_statement(table, schema, columns, partition_bounds),
            "Query",
        )

    def _handle_pandas_output(self, obj: PandasDataFrame, schema: str, table: str):
        from snowflake import connector  # pylint: disable=no-name-in-module

        yield MetadataEntry.int(obj.shape[0], "Rows")
        yield MetadataEntry.md(pandas_columns_to_markdown(obj), "DataFrame columns")

        connector.paramstyle = "pyformat"
        with connect_snowflake(config=self._config, schema=schema) as con:
            with_uppercase_cols = obj.rename(str.upper, copy=False, axis="columns")
            with_uppercase_cols.to_sql(
                table,
                con=con,
                if_exists="append",
                index=False,
                method=pd_writer,
            )

    def _handle_spark_output(self, df: SparkDataFrame, schema: str, table: str):
        options = {
            "sfURL": f"{self._config['account']}.snowflakecomputing.com",
            "sfUser": self._config["user"],
            "sfPassword": self._config["password"],
            "sfDatabase": self._config["database"],
            "sfSchema": schema,
            "sfWarehouse": self._config["warehouse"],
            "dbtable": table,
        }
        yield MetadataEntry.md(spark_columns_to_markdown(df.schema), "DataFrame columns")

        df.write.format("net.snowflake.spark.snowflake").options(**options).mode("append").save()

    def _get_cleanup_statement(
        self, table: str, schema: str, partition_bounds: Mapping[str, str]
    ) -> str:
        """
        Returns a SQL statement that deletes data in the given table to make way for the output data
        being written.
        """
        if partition_bounds:
            return f"DELETE FROM {schema}.{table} {self._partition_where_clause(partition_bounds)}"
        else:
            return f"DELETE FROM {schema}.{table}"

    def load_input(self, context: InputContext) -> PandasDataFrame:
        metadata: Mapping[str, Any]
        if context.upstream_output is not None:
            # loading from an upstream output
            metadata = check.not_none(context.upstream_output.metadata)
        else:
            # loading as a root input
            metadata = check.not_none(context.metadata)

        schema, table = metadata["table"].split(".")
        with connect_snowflake(config=self._config) as con:
            result = read_sql(
                sql=self._get_select_statement(
                    table,
                    schema,
                    metadata.get("columns"),
                    context.resources.partition_bounds
                    if metadata.get("partitioned") is True
                    else None,
                ),
                con=con,
            )
            result.columns = map(str.lower, result.columns)
            return result

    def _get_select_statement(
        self,
        table: str,
        schema: str,
        columns: Optional[Sequence[str]],
        partition_bounds: Optional[Mapping[str, str]],
    ):
        col_str = ", ".join(columns) if columns else "*"
        if partition_bounds:
            return (
                f"""SELECT * FROM {self._config["database"]}.{schema}.{table}\n"""
                + self._partition_where_clause(partition_bounds)
            )
        else:
            return f"""SELECT {col_str} FROM {schema}.{table}"""

    def _partition_where_clause(self, partition_bounds: Mapping[str, str]) -> str:
        return f"""WHERE TO_TIMESTAMP(time::INT) BETWEEN '{partition_bounds["start"]}' AND '{partition_bounds["end"]}'"""

    def get_output_asset_key(self, context: OutputContext) -> AssetKey:
        metadata = check.not_none(context.metadata)
        return AssetKey(["snowflake", *cast(str, metadata["table"]).split(".")])

    def get_output_asset_partitions(self, context: OutputContext):
        metadata = check.not_none(context.metadata)
        if metadata.get("partitioned") is True:
            return [context.resources.partition_bounds["start"]]
        else:
            return None


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
