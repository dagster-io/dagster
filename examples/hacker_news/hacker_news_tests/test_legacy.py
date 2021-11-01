import tempfile

from dagster import execute_pipeline
from hacker_news.legacy.pipelines.download_pipeline import download_pipeline
from hacker_news.legacy.pipelines.story_recommender import (  # pylint: disable=unused-import
    story_recommender,
)
from hacker_news.legacy.repo import hacker_news_legacy  # pylint: disable=unused-import


def test_download():
    with tempfile.TemporaryDirectory() as temp_dir:
        result = execute_pipeline(
            download_pipeline,
            run_config={
                "resources": {
                    "partition_bounds": {
                        "config": {"start": "2020-12-30 00:00:00", "end": "2020-12-30 01:00:00"}
                    },
                    "parquet_io_manager": {"config": {"base_path": temp_dir}},
                    "warehouse_io_manager": {"config": {"base_path": temp_dir}},
                }
            },
            mode="test_local_data",
        )

        assert result.success
