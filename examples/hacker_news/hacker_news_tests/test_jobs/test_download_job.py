import tempfile

from dagster import ResourceDefinition, fs_io_manager
from hacker_news.jobs.hacker_news_api_download import (
    configured_pyspark,
    hacker_news_api_download,
    hourly_download_config,
)
from hacker_news.resources.hn_resource import hn_snapshot_client
from hacker_news.resources.parquet_io_manager import partitioned_parquet_io_manager


def test_download():

    with tempfile.TemporaryDirectory() as temp_dir:
        result = hacker_news_api_download.to_job(
            resource_defs={
                "io_manager": fs_io_manager,
                "partition_start": ResourceDefinition.string_resource(),
                "partition_end": ResourceDefinition.string_resource(),
                "parquet_io_manager": partitioned_parquet_io_manager.configured(
                    {"base_path": temp_dir}
                ),
                "warehouse_io_manager": partitioned_parquet_io_manager.configured(
                    {"base_path": temp_dir}
                ),
                "pyspark": configured_pyspark,
                "hn_client": hn_snapshot_client,
            },
            config=hourly_download_config,
        ).execute_in_process(partition_key="2020-12-30-01:00")

        assert result.success
