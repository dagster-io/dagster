import os

import pytest
import duckdb
from dagster_duckdb.io_manager import build_duckdb_io_manager
from dagster_duckdb_pyspark import DuckDBPySparkTypeHandler
from pyspark.sql import DataFrame as SparkDF
from pyspark.sql import SparkSession

from dagster import asset, graph, materialize, op, DailyPartitionsDefinition
from dagster._check import CheckError


@op
def a_df() -> SparkDF:
    spark = SparkSession.builder.getOrCreate()
    data = [(1, 4), (2, 5), (3, 6)]
    return spark.createDataFrame(data)


@graph
def make_df():
    a_df()


def test_duckdb_io_manager_with_ops_spark(tmp_path):
    duckdb_io_manager = build_duckdb_io_manager([DuckDBPySparkTypeHandler()])
    resource_defs = {
        "io_manager": duckdb_io_manager.configured(
            {"duckdb_path": os.path.join(tmp_path, "unit_test.duckdb")}
        ),
    }

    job = make_df.to_job(resource_defs=resource_defs)

    res = job.execute_in_process()

    assert res.success


@asset(key_prefix=["my_schema"])
def b_df() -> SparkDF:
    spark = SparkSession.builder.getOrCreate()
    data = [(1, 4), (2, 5), (3, 6)]
    return spark.createDataFrame(data)


def test_duckdb_io_manager_with_assets_spark(tmp_path):
    duckdb_io_manager = build_duckdb_io_manager([DuckDBPySparkTypeHandler()])
    resource_defs = {
        "io_manager": duckdb_io_manager.configured(
            {"duckdb_path": os.path.join(tmp_path, "unit_test.duckdb")}
        ),
    }

    res = materialize([b_df], resources=resource_defs)
    assert res.success


@op
def non_supported_type() -> int:
    return 1


@graph
def not_supported():
    non_supported_type()


def test_not_supported_type(tmp_path):
    duckdb_io_manager = build_duckdb_io_manager([DuckDBPySparkTypeHandler()])
    resource_defs = {
        "io_manager": duckdb_io_manager.configured(
            {"duckdb_path": os.path.join(tmp_path, "unit_test.duckdb")}
        ),
    }

    job = not_supported.to_job(resource_defs=resource_defs)

    with pytest.raises(
        CheckError,
        match="DuckDBIOManager does not have a handler that supports outputs of type '<class 'int'>'",
    ):
        job.execute_in_process()


@asset(key_prefix=["my_schema"])
def upstream() -> SparkDF:
    spark = SparkSession.builder.getOrCreate()
    data = [(1, 4), (2, 5), (3, 6)]
    return spark.createDataFrame(data)


@asset(key_prefix=["my_schema"])
def downstream(upstream: SparkDF) -> SparkDF:
    return upstream


def test_cant_load_input(tmp_path):
    duckdb_io_manager = build_duckdb_io_manager([DuckDBPySparkTypeHandler()])
    resource_defs = {
        "io_manager": duckdb_io_manager.configured(
            {"duckdb_path": os.path.join(tmp_path, "unit_test.duckdb")}
        ),
    }

    with pytest.raises(
        CheckError,
        match="DuckDBIOManager does not have a handler that supports inputs of type",
    ):
        materialize([upstream, downstream], resources=resource_defs)


@asset(
    partitions_def=DailyPartitionsDefinition(start_date="2022-01-01"),
    key_prefix=["my_schema"]
)
def daily_partitioned(context):
    partition = context.asset_partition_key_for_output()[-1]
    context.log.info(f"PARTITION KEY {partition} {type(partition)}")
    spark = SparkSession.builder.getOrCreate()
    data = [(partition, 4), (partition, 5), (partition, 6)]
    return spark.createDataFrame(data)

def test_partitioned_asset(tmp_path):
    duckdb_io_manager = build_duckdb_io_manager([DuckDBPySparkTypeHandler()]).configured(
            {"duckdb_path": os.path.join(tmp_path, "unit_test.duckdb"), "base_path": "/Users/jamie/dev/test_outs"}
        )
    resource_defs = {
        "io_manager": duckdb_io_manager
    }

    materialize([daily_partitioned], partition_key="2022-01-01", resources=resource_defs)

    duckdb_conn = duckdb.connect(database=os.path.join(tmp_path, "unit_test.duckdb"))

    out_df = duckdb_conn.execute("SELECT * FROM my_schema.daily_partitioned").fetch_df()
    print(out_df)

    assert out_df["_1"].tolist() == ['1', '1', '1']

    materialize([daily_partitioned], partition_key="2022-01-02", resources=resource_defs)

    duckdb_conn = duckdb.connect(database=os.path.join(tmp_path, "unit_test.duckdb"))

    out_df = duckdb_conn.execute("SELECT * FROM my_schema.daily_partitioned").fetch_df()
    print(out_df)

    assert out_df["_1"].tolist() == ['1', '1', '1', '2', '2', '2']