import tempfile

from dagster import execute_pipeline
from hacker_news.pipelines.download_pipeline import download_pipeline


def test_download():
    with tempfile.TemporaryDirectory() as temp_dir:
        result = execute_pipeline(
            download_pipeline,
            run_config={
                "resources": {
                    "partition_start": {"config": "2020-12-30 00:00:00"},
                    "partition_end": {"config": "2020-12-30 01:00:00"},
                    "parquet_io_manager": {"config": {"base_path": temp_dir}},
                    "warehouse_io_manager": {"config": {"base_path": temp_dir}},
                }
            },
            mode="test_local_data",
        )

        assert result.success
