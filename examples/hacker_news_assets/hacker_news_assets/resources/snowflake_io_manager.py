import os
import textwrap
from contextlib import contextmanager
from datetime import datetime
from typing import Optional, Sequence, Tuple, Union

from pandas import DataFrame as PandasDataFrame
from pandas import read_sql
from pyspark.sql import DataFrame as SparkDataFrame
from pyspark.sql.types import StructField, StructType
from snowflake.connector.pandas_tools import pd_writer
from snowflake.sqlalchemy import URL  # pylint: disable=no-name-in-module,import-error
from sqlalchemy import create_engine

from dagster import IOManager, InputContext, MetadataEntry, OutputContext
from dagster import _check as check
from dagster import io_manager

SNOWFLAKE_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


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


@io_manager(config_schema={"database": str})
def snowflake_io_manager(init_context):
    return SnowflakeIOManager(
        config=dict(database=init_context.resource_config["database"], **SHARED_SNOWFLAKE_CONF)
    )


class SnowflakeIOManager(IOManager):
    """
    This IOManager can handle outputs that are either Spark or Pandas DataFrames. In either case,
    the data will be written to a Snowflake table specified by metadata on the relevant Out.
    """

    def __init__(self, config):
        self._config = config

    def handle_output(self, context: OutputContext, obj: Union[PandasDataFrame, SparkDataFrame]):
        schema, table = context.asset_key.path[-2], context.asset_key.path[-1]  # type: ignore

        time_window = context.asset_partitions_time_window if context.has_asset_partitions else None
        with connect_snowflake(config=self._config, schema=schema) as con:
            con.execute(self._get_cleanup_statement(table, schema, time_window))

        if isinstance(obj, SparkDataFrame):
            yield from self._handle_spark_output(obj, schema, table)
        elif isinstance(obj, PandasDataFrame):
            yield from self._handle_pandas_output(obj, schema, table)
        elif obj is None:  # dbt
            config = dict(SHARED_SNOWFLAKE_CONF)
            config["schema"] = schema
            with connect_snowflake(config=config) as con:
                df = read_sql(f"SELECT * FROM {context.name} LIMIT 5", con=con)
                num_rows = con.execute(f"SELECT COUNT(*) FROM {context.name}").fetchone()

            yield MetadataEntry.md(df.to_markdown(), "Data sample")
            yield MetadataEntry.int(num_rows, "Rows")
        else:
            raise Exception(
                "SnowflakeIOManager only supports pandas DataFrames and spark DataFrames"
            )

        yield MetadataEntry.text(
            self._get_select_statement(
                table,
                schema,
                None,
                time_window,
            ),
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
        self, table: str, schema: str, time_window: Optional[Tuple[datetime, datetime]]
    ) -> str:
        """
        Returns a SQL statement that deletes data in the given table to make way for the output data
        being written.
        """
        if time_window:
            return f"DELETE FROM {schema}.{table} {self._time_window_where_clause(time_window)}"
        else:
            return f"DELETE FROM {schema}.{table}"

    def load_input(self, context: InputContext) -> PandasDataFrame:
        upstream_output = check.not_none(context.upstream_output)
        asset_key = check.not_none(upstream_output.asset_key)

        schema, table = asset_key.path[-2], asset_key.path[-1]
        with connect_snowflake(config=self._config) as con:
            result = read_sql(
                sql=self._get_select_statement(
                    table,
                    schema,
                    (context.metadata or {}).get("columns"),
                    context.asset_partitions_time_window if context.has_asset_partitions else None,
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
        time_window: Optional[Tuple[datetime, datetime]],
    ):
        col_str = ", ".join(columns) if columns else "*"
        if time_window:
            return (
                f"""SELECT * FROM {self._config["database"]}.{schema}.{table}\n"""
                + self._time_window_where_clause(time_window)
            )
        else:
            return f"""SELECT {col_str} FROM {schema}.{table}"""

    def _time_window_where_clause(self, time_window: Tuple[datetime, datetime]) -> str:
        start_dt, end_dt = time_window
        return f"""WHERE TO_TIMESTAMP(time::INT) BETWEEN '{start_dt.strftime(SNOWFLAKE_DATETIME_FORMAT)}' AND '{end_dt.strftime(SNOWFLAKE_DATETIME_FORMAT)}'"""


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
