import os

import pandas as pd
import pytest
from dagster_duckdb.io_manager import build_duckdb_io_manager
from dagster_duckdb.type_handlers import DuckDBPandasTypeHandler, DuckDBPySparkTypeHandler
from pyspark.sql import DataFrame as SparkDF
from pyspark.sql import SparkSession

from dagster import asset, graph, materialize, op
from dagster._check import CheckError


@op
def a_df() -> pd.DataFrame:
    return pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})


@op
def add_one(df: pd.DataFrame):
    return df + 1


@graph
def add_one_to_dataframe():
    add_one(a_df())


def test_duckdb_io_manager_with_ops(tmp_path):
    duckdb_io_manager = build_duckdb_io_manager([DuckDBPandasTypeHandler()])
    resource_defs = {
        "io_manager": duckdb_io_manager.configured(
            {"duckdb_path": os.path.join(tmp_path, "unit_test.duckdb")}
        ),
    }

    job = add_one_to_dataframe.to_job(resource_defs=resource_defs)

    res = job.execute_in_process()

    assert res.success


@asset(key_prefix=["my_schema"])
def b_df() -> pd.DataFrame:
    return pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})


@asset(key_prefix=["my_schema"])
def b_plus_one(b_df: pd.DataFrame):
    return b_df + 1


def test_duckdb_io_manager_with_assets(tmp_path):
    duckdb_io_manager = build_duckdb_io_manager([DuckDBPandasTypeHandler()])
    resource_defs = {
        "io_manager": duckdb_io_manager.configured(
            {"duckdb_path": os.path.join(tmp_path, "unit_test.duckdb")}
        ),
    }

    res = materialize([b_df, b_plus_one], resources=resource_defs)
    assert res.success


@op
def non_supported_type() -> int:
    return 1


@graph
def not_supported():
    non_supported_type()


def test_not_supported_type(tmp_path):
    duckdb_io_manager = build_duckdb_io_manager([DuckDBPandasTypeHandler()])
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


@op
def a_df_spark() -> SparkDF:
    spark = SparkSession.builder.getOrCreate()
    return spark.createDataFrame(pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]}))


@graph
def add_one_to_dataframe_spark():
    add_one(a_df_spark())


def test_duckdb_io_manager_with_ops_spark(tmp_path):
    duckdb_io_manager = build_duckdb_io_manager(
        [DuckDBPandasTypeHandler(), DuckDBPySparkTypeHandler()]
    )
    resource_defs = {
        "io_manager": duckdb_io_manager.configured(
            {"duckdb_path": os.path.join(tmp_path, "unit_test.duckdb")}
        ),
    }

    job = add_one_to_dataframe_spark.to_job(resource_defs=resource_defs)

    res = job.execute_in_process()

    assert res.success


@asset(key_prefix=["my_schema"])
def b_df_spark() -> SparkDF:
    spark = SparkSession.builder.getOrCreate()
    return spark.createDataFrame(pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]}))


@asset(key_prefix=["my_schema"])
def b_plus_one_spark(b_df_spark: pd.DataFrame):
    return b_df_spark + 1


def test_duckdb_io_manager_with_assets_spark(tmp_path):
    duckdb_io_manager = build_duckdb_io_manager(
        [DuckDBPandasTypeHandler(), DuckDBPySparkTypeHandler()]
    )
    resource_defs = {
        "io_manager": duckdb_io_manager.configured(
            {"duckdb_path": os.path.join(tmp_path, "unit_test.duckdb")}
        ),
    }

    res = materialize([b_df_spark, b_plus_one_spark], resources=resource_defs)
    assert res.success
