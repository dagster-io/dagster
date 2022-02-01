import tempfile

from dagster import ResourceDefinition, fs_io_manager, mem_io_manager
from dagster.core.asset_defs import build_assets_job
from dagster_pyspark import pyspark_resource
from hacker_news_assets.jobs.hacker_news_api_download import ASSETS
from hacker_news_assets.resources.hn_resource import hn_snapshot_client
from hacker_news_assets.resources.parquet_io_manager import local_partitioned_parquet_io_manager


def test_download():
    with tempfile.TemporaryDirectory() as temp_dir:
        test_job = build_assets_job(
            "test_job",
            assets=ASSETS,
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
            },
        )
        result = test_job.execute_in_process(partition_key="2020-12-30-00:00")

        assert result.success
