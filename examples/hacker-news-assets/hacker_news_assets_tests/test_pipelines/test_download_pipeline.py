import tempfile

from dagster import ResourceDefinition, fs_io_manager, mem_io_manager
from dagster_pyspark import pyspark_resource
from hacker_news_assets.pipelines.download_pipeline import download_comments_and_stories_dev
from hacker_news_assets.resources.hn_resource import hn_snapshot_client
from hacker_news_assets.resources.parquet_io_manager import partitioned_parquet_io_manager


def test_download():
    with tempfile.TemporaryDirectory() as temp_dir:
        result = download_comments_and_stories_dev.graph.execute_in_process(
            run_config={
                "resources": {
                    "partition_start": {"config": "2020-12-30 00:00:00"},
                    "partition_end": {"config": "2020-12-30 01:00:00"},
                    "parquet_io_manager": {"config": {"base_path": temp_dir}},
                }
            },
            resources={
                "io_manager": fs_io_manager,
                "partition_start": ResourceDefinition.string_resource(),
                "partition_end": ResourceDefinition.string_resource(),
                "parquet_io_manager": partitioned_parquet_io_manager,
                "warehouse_io_manager": mem_io_manager,
                "pyspark": pyspark_resource,
                "hn_client": hn_snapshot_client,
            },
        )

        assert result.success
