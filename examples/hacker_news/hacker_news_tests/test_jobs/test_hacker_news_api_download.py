import tempfile

from dagster import fs_io_manager
from hacker_news.jobs.hacker_news_api_download import hacker_news_api_download
from hacker_news.partitions import hourly_partitions
from hacker_news.resources import configured_pyspark
from hacker_news.resources.hn_resource import hn_snapshot_client
from hacker_news.resources.parquet_io_manager import local_partitioned_parquet_io_manager


def test_download():

    with tempfile.TemporaryDirectory() as temp_dir:
        result = hacker_news_api_download.to_job(
            resource_defs={
                "io_manager": fs_io_manager,
                "parquet_io_manager": local_partitioned_parquet_io_manager.configured(
                    {"base_path": temp_dir}
                ),
                "warehouse_io_manager": local_partitioned_parquet_io_manager.configured(
                    {"base_path": temp_dir}
                ),
                "pyspark": configured_pyspark,
                "hn_client": hn_snapshot_client,
            },
            partitions_def=hourly_partitions,
        ).execute_in_process(partition_key="2020-12-30-01:00")

        assert result.success
