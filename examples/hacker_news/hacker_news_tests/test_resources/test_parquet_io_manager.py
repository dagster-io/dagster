import os
import tempfile

import pandas
from dagster import Out, ResourceDefinition, graph, op
from dagster_pyspark import pyspark_resource
from hacker_news.resources.parquet_io_manager import partitioned_parquet_io_manager
from pyspark.sql import DataFrame as SparkDF


@op(out={"out": Out(io_manager_key="pandas_to_spark")})
def emit_pandas_df(_):
    return pandas.DataFrame({"foo": ["bar", "baz"], "quux": [1, 2]})


@op
def read_pandas_df_to_spark(_, df: SparkDF):
    assert isinstance(df, SparkDF)
    assert df.count() == 2
    assert set(df.columns) == {"foo", "quux"}


@graph
def io_manager_test_pipeline():
    read_pandas_df_to_spark(emit_pandas_df())


def test_io_manager():
    with tempfile.TemporaryDirectory() as temp_dir:
        expected_path = os.path.join(temp_dir, "out-1_2.pq")
        res = io_manager_test_pipeline.to_job(
            resource_defs={
                "pyspark": pyspark_resource,
                "pandas_to_spark": partitioned_parquet_io_manager,
                "partition_start": ResourceDefinition.hardcoded_resource("1"),
                "partition_end": ResourceDefinition.hardcoded_resource("2"),
            }
        ).execute_in_process(
            run_config={"resources": {"pandas_to_spark": {"config": {"base_path": temp_dir}}}}
        )
        assert res.success
        assert os.path.exists(expected_path)
        intermediate_df = pandas.read_parquet(expected_path)
        assert all(intermediate_df == pandas.DataFrame({"foo": ["bar", "baz"], "quux": [1, 2]}))
