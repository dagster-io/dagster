from dagster import ModeDefinition, PresetDefinition, pipeline
from dagster.seven.temp_dir import get_system_temp_directory
from hacker_news.ops.download_items import build_comments, build_stories, download_items
from hacker_news.ops.id_range_for_time import id_range_for_time
from hacker_news.resources import RESOURCES_LOCAL, RESOURCES_PROD, RESOURCES_STAGING
from hacker_news.resources.hn_resource import hn_api_subsample_client, hn_snapshot_client
from hacker_news.resources.partition_bounds import partition_bounds

MODE_TEST = ModeDefinition(
    name="test_local_data",
    description="This mode queries snapshotted HN data and does all writes locally.",
    resource_defs=dict(
        {"partition_bounds": partition_bounds, "hn_client": hn_snapshot_client},
        **RESOURCES_LOCAL,
    ),
)


MODE_STAGING = ModeDefinition(
    name="staging_live_data",
    description=(
        "This mode queries live HN data and writes to a staging S3 bucket. "
        "Intended for use in the staging environment."
    ),
    resource_defs=dict(
        **{
            "partition_bounds": partition_bounds,
            "hn_client": hn_api_subsample_client.configured({"sample_rate": 10}),
        },
        **RESOURCES_STAGING,
    ),
)


MODE_PROD = ModeDefinition(
    name="prod",
    description=(
        "This mode queries live HN data and writes to a prod S3 bucket."
        "Intended for use in production."
    ),
    resource_defs=dict(
        **{
            "partition_bounds": partition_bounds,
            "hn_client": hn_api_subsample_client.configured({"sample_rate": 10}),
        },
        **RESOURCES_PROD,
    ),
)


DEFAULT_PARTITION_RESOURCE_CONFIG = {
    "partition_bounds": {"config": {"start": "2020-12-30 00:00:00", "end": "2020-12-30 01:00:00"}},
}

PRESET_TEST = PresetDefinition(
    name="test_local_data",
    run_config={
        "resources": dict(
            parquet_io_manager={"config": {"base_path": get_system_temp_directory()}},
            warehouse_io_manager={"config": {"base_path": get_system_temp_directory()}},
            **DEFAULT_PARTITION_RESOURCE_CONFIG,
        ),
    },
    mode="test_local_data",
)


@pipeline(
    mode_defs=[
        MODE_TEST,
        MODE_STAGING,
        MODE_PROD,
    ],
    tags={
        "dagster-k8s/config": {
            "container_config": {
                "resources": {
                    "requests": {"cpu": "500m", "memory": "2Gi"},
                }
            },
        }
    },
    preset_defs=[PRESET_TEST],
)
def download_pipeline():
    """
    #### Owners
    schrockn@elementl.com, cat@elementl.com

    #### About
    Downloads all items from the HN API for a given day,
    splits the items into stories and comment types using Spark, and uploads filtered items to
    the corresponding stories or comments Snowflake table
    """
    items = download_items(id_range_for_time())
    build_comments(items)
    build_stories(items)
