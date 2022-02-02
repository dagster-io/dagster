# pylint: disable=redefined-outer-name
import os
import tempfile

import pandas
from dagster.core.asset_defs import asset, build_assets_job
from dagster_pyspark import pyspark_resource
from hacker_news_assets.partitions import hourly_partitions
from hacker_news_assets.resources.parquet_io_manager import local_partitioned_parquet_io_manager
from pyspark.sql import DataFrame as SparkDF


def test_io_manager():
    df_value = pandas.DataFrame({"foo": ["bar", "baz"], "quux": [1, 2]})

    @asset(partitions_def=hourly_partitions)
    def pandas_df_asset():
        return df_value

    @asset(partitions_def=hourly_partitions)
    def spark_input_asset(pandas_df_asset: SparkDF):
        assert isinstance(pandas_df_asset, SparkDF)
        assert pandas_df_asset.count() == 2
        assert set(pandas_df_asset.columns) == {"foo", "quux"}
        return pandas_df_asset

    with tempfile.TemporaryDirectory() as temp_dir:
        io_manager_test_job = build_assets_job(
            "io_manager_test_job",
            assets=[pandas_df_asset, spark_input_asset],
            resource_defs={
                "pyspark": pyspark_resource,
                "io_manager": local_partitioned_parquet_io_manager.configured(
                    {"base_path": temp_dir}
                ),
            },
        )

        expected_path = os.path.join(temp_dir, "pandas_df_asset-20220101160000_20220101170000.pq")
        res = io_manager_test_job.execute_in_process(partition_key="2022-01-01-16:00")
        assert res.success
        assert os.path.exists(expected_path)
        intermediate_df = pandas.read_parquet(expected_path)
        assert all(intermediate_df == df_value)
