from dagster import graph, in_process_executor
from hacker_news.ops.download_items import build_comments, build_stories, download_items
from hacker_news.ops.id_range_for_time import id_range_for_time
from hacker_news.partitions import hourly_partitions

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


download_prod_job = hacker_news_api_download.to_job(
    tags=DOWNLOAD_TAGS, partitions_def=hourly_partitions
)


download_staging_job = hacker_news_api_download.to_job(
    tags=DOWNLOAD_TAGS, partitions_def=hourly_partitions
)

download_local_job = hacker_news_api_download.to_job(
    partitions_def=hourly_partitions, executor_def=in_process_executor
)
