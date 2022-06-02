from hacker_news.ops.download_items import build_comments, build_stories, download_items
from hacker_news.ops.id_range_for_time import id_range_for_time
from hacker_news.resources.hn_resource import hn_api_subsample_client, hn_snapshot_client
from hacker_news.resources.partition_bounds import partition_bounds
from hacker_news.schedules.hourly_hn_download_schedule import hourly_download_config
from ..sensors.hn_tables_updated_sensor import make_hn_tables_updated_sensor

from dagster import graph, in_process_executor, build_schedule_from_partitions

DOWNLOAD_TAGS = {
    "dagster-k8s/config": {
        "container_config": {
            "resources": {
                "requests": {"cpu": "500m", "memory": "2Gi"},
            }
        },
    }
}


@graph
def hacker_news_api_download():
    """
    #### Owners
    schrockn@elementl.com, max@elementl.com

    #### About
    Downloads all items from the HN API for a given day,
    splits the items into stories and comment types using Spark, and uploads filtered items to
    the corresponding stories or comments Snowflake table
    """
    items = download_items(id_range_for_time())
    build_comments(items)
    build_stories(items)


download_prod_job = hacker_news_api_download.to_pending_job(
    resource_defs={
        "partition_bounds": partition_bounds,
        "hn_client": hn_api_subsample_client.configured({"sample_rate": 10}),
    },
    tags=DOWNLOAD_TAGS,
    config=hourly_download_config,
)


download_staging_job = hacker_news_api_download.to_pending_job(
    resource_defs={
        "partition_bounds": partition_bounds,
        "hn_client": hn_api_subsample_client.configured({"sample_rate": 10}),
    },
    tags=DOWNLOAD_TAGS,
    config=hourly_download_config,
)

download_local_job = hacker_news_api_download.to_pending_job(
    resource_defs={"partition_bounds": partition_bounds, "hn_client": hn_snapshot_client},
    config={
        "resources": {
            "partition_bounds": {
                "config": {
                    "start": "2020-12-30 00:00:00",
                    "end": "2020-12-30 01:00:00",
                }
            },
        }
    },
    executor_def=in_process_executor,
)

download_schedule = build_schedule_from_partitions(
    job_name="download_job", partitions=hourly_download_config.partitions_def
)
