import tempfile

from dagster_pyspark import pyspark_resource
from hacker_news_assets.recommender import recommender_assets
from hacker_news_assets.resources.parquet_io_manager import local_partitioned_parquet_io_manager
from hacker_news_assetse.resources.hn_resource import hn_snapshot_client
from pandas import DataFrame

from dagster import AssetKey, ResourceDefinition, fs_io_manager, mem_io_manager


def test_download():
    with tempfile.TemporaryDirectory() as temp_dir:
        test_job = recommender_assets.build_job(
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

        comments = DataFrame(
            [[2, 1000, "bob"], [3, 2, "alice"]], columns=["id", "parent", "user_id"]
        )
        stories = DataFrame([[1000]], columns=["id"])

        result = test_job.execute_in_process(
            asset_values={
                AssetKey(["core", "comments"]): comments,
                AssetKey(["core", "stories"]): stories,
            }
        )

        assert result.success
