import tempfile

from dagster import ResourceDefinition, fs_io_manager
from hacker_news.jobs.download_job import configured_pyspark, download_graph
from hacker_news.resources.hn_resource import hn_snapshot_client
from hacker_news.resources.parquet_io_manager import partitioned_parquet_io_manager


def test_download():

    with tempfile.TemporaryDirectory() as temp_dir:
        result = download_graph.to_job(
            resource_defs={
                "io_manager": fs_io_manager,
                "partition_start": ResourceDefinition.string_resource(),
                "partition_end": ResourceDefinition.string_resource(),
                "parquet_io_manager": partitioned_parquet_io_manager,
                "warehouse_io_manager": partitioned_parquet_io_manager,
                "pyspark": configured_pyspark,
                "hn_client": hn_snapshot_client,
            }
        ).execute_in_process(
            run_config={
                "resources": {
                    "partition_start": {"config": "2020-12-30 00:00:00"},
                    "partition_end": {"config": "2020-12-30 01:00:00"},
                    "parquet_io_manager": {"config": {"base_path": temp_dir}},
                    "warehouse_io_manager": {"config": {"base_path": temp_dir}},
                }
            },
        )

        assert result.success
