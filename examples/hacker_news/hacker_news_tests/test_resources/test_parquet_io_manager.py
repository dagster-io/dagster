import os
import tempfile

import pandas
from dagster import Out, graph, op
from dagster_pyspark import pyspark_resource
from hacker_news.partitions import hourly_partitions
from hacker_news.resources.parquet_io_manager import local_partitioned_parquet_io_manager
from pyspark.sql import DataFrame as SparkDF


@op(out={"out": Out(io_manager_key="parquet_io_manager")})
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
                "parquet_io_manager": local_partitioned_parquet_io_manager.configured(
                    {"base_path": temp_dir}
                ),
            },
            partitions_def=hourly_partitions,
        ).execute_in_process(partition_key={"2020-12-30-00:00"})
        assert res.success
        assert os.path.exists(expected_path)
        intermediate_df = pandas.read_parquet(expected_path)
        assert all(intermediate_df == pandas.DataFrame({"foo": ["bar", "baz"], "quux": [1, 2]}))
