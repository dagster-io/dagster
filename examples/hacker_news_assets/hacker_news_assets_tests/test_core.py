import tempfile

from dagster_pyspark import pyspark_resource
from hacker_news_assets.core import core_assets
from hacker_news_assets.resources.parquet_io_manager import local_partitioned_parquet_io_manager
from hacker_news_assetse.resources.hn_resource import hn_snapshot_client

from dagster import ResourceDefinition, fs_io_manager, mem_io_manager


def test_download():
    with tempfile.TemporaryDirectory() as temp_dir:
        test_job = core_assets.build_job(
            "test_job",
            resource_defs={
                "io_manager": fs_io_manager,
                "partition_start": ResourceDefinition.string_resource(),
                "partition_end": ResourceDefinition.string_resource(),
                "parquet_io_manager": local_partitioned_parquet_io_manager.configured(
                    {"base_path": temp_dir}
                ),
                "warehouse_io_manager": mem_io_manager,
                "pyspark": pyspark_resource,
                "hn_client": hn_snapshot_client,
                "dbt": ResourceDefinition.none_resource(),
            },
        )

        result = test_job.execute_in_process(partition_key="2020-12-30-00:00")

        assert result.success
