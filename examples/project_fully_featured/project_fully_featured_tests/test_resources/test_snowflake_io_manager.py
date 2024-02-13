import os
import uuid
from contextlib import contextmanager
from typing import Iterator

import pytest
from dagster import AssetKey, asset, build_input_context, build_output_context
from dagster._core.execution.context.input import InputContext
from dagster._core.execution.context.output import OutputContext
from pandas import DataFrame as PandasDataFrame
from pyspark.sql import Row, SparkSession
from pyspark.sql.types import IntegerType, StringType, StructField, StructType

from project_fully_featured.resources import SHARED_SNOWFLAKE_CONF
from project_fully_featured.resources.snowflake_io_manager import (
    SnowflakeIOManager,
    connect_snowflake,
)


def mock_output_context(asset_key: AssetKey) -> OutputContext:
    @asset(name=asset_key.path[-1], key_prefix=asset_key.path[:-1])
    def my_asset():
        pass

    return build_output_context(op_def=my_asset.op, name="result", asset_key=asset_key)


def mock_input_context(upstream_output_context: OutputContext) -> InputContext:
    return build_input_context(
        upstream_output=upstream_output_context,
        name=upstream_output_context.name,
        asset_key=upstream_output_context.asset_key,
    )


@contextmanager
def temporary_snowflake_table(contents: PandasDataFrame) -> Iterator[AssetKey]:
    schema = "hackernews"
    snowflake_config = dict(
        database="BEN",
        **SHARED_SNOWFLAKE_CONF,
    )
    table_name = "a" + str(uuid.uuid4()).replace("-", "_")
    with connect_snowflake(snowflake_config) as con:
        contents.to_sql(name=table_name, con=con, index=False, schema=schema)
    try:
        yield AssetKey([schema, table_name])
    finally:
        with connect_snowflake(snowflake_config) as conn:
            conn.execute(f"drop table {schema}.{table_name}")


@pytest.mark.skipif(
    os.environ.get("TEST_SNOWFLAKE") != "true",
    reason="avoid dependency on snowflake for tests",
)
def test_handle_output_then_load_input_pandas():
    snowflake_manager = SnowflakeIOManager(database="BEN", **SHARED_SNOWFLAKE_CONF)
    contents1 = PandasDataFrame([{"col1": "a", "col2": 1}])  # just to get the types right
    contents2 = PandasDataFrame([{"col1": "b", "col2": 2}])  # contents we will insert
    with temporary_snowflake_table(contents1) as temp_table_key:
        output_context = mock_output_context(asset_key=temp_table_key)
        snowflake_manager.handle_output(output_context, contents2)

        input_context = mock_input_context(output_context)
        input_value = snowflake_manager.load_input(input_context)
        assert input_value.equals(contents2), f"{input_value}\n\n{contents2}"


@pytest.mark.skipif(
    os.environ.get("TEST_SNOWFLAKE") != "true",
    reason="avoid dependency on snowflake for tests",
)
def test_handle_output_spark_then_load_input_pandas():
    snowflake_manager = SnowflakeIOManager(database="BEN", **SHARED_SNOWFLAKE_CONF)
    spark = SparkSession.builder.config(
        "spark.jars.packages",
        "net.snowflake:snowflake-jdbc:3.8.0,net.snowflake:spark-snowflake_2.12:2.8.2-spark_3.0",
    ).getOrCreate()

    schema = StructType([StructField("col1", StringType()), StructField("col2", IntegerType())])
    contents = spark.createDataFrame([Row(col1="Thom", col2=51)], schema)

    with temporary_snowflake_table(PandasDataFrame([{"col1": "a", "col2": 1}])) as temp_table_key:
        output_context = mock_output_context(asset_key=temp_table_key)
        snowflake_manager.handle_output(output_context, contents)

        input_context = mock_input_context(output_context)
        input_value = snowflake_manager.load_input(input_context)
        contents_pandas = contents.toPandas()
        assert str(input_value) == str(contents_pandas), f"{input_value}\n\n{contents_pandas}"
