import os

import pytest
from dagster_duckdb.io_manager import build_duckdb_io_manager
from dagster_duckdb_pyspark import DuckDBPySparkTypeHandler
from pyspark.sql import DataFrame as SparkDF
from pyspark.sql import SparkSession

from dagster import asset, graph, materialize, op
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
