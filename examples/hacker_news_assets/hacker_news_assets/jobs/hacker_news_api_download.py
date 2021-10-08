from datetime import datetime

from dagster import hourly_partitioned_config, in_process_executor
from dagster.core.asset_defs import build_assets_job
from hacker_news_assets.assets.id_range_for_time import id_range_for_time
from hacker_news_assets.assets.items import comments, items, stories
from hacker_news_assets.resources import RESOURCES_LOCAL, RESOURCES_PROD, RESOURCES_STAGING
from hacker_news_assets.resources.hn_resource import hn_api_subsample_client, hn_snapshot_client
from hacker_news_assets.resources.partition_bounds import partition_bounds

DOWNLOAD_TAGS = {
    "dagster-k8s/config": {
        "container_config": {
            "resources": {
                "requests": {"cpu": "500m", "memory": "2Gi"},
            }
        },
    }
}


@hourly_partitioned_config(start_date=datetime(2020, 12, 1))
def hourly_download_config(start: datetime, end: datetime):
    return {
        "resources": {
            "partition_bounds": {
                "config": {
                    "start": start.strftime("%Y-%m-%d %H:%M:%S"),
                    "end": end.strftime("%Y-%m-%d %H:%M:%S"),
                }
            },
        }
    }


ASSETS = [id_range_for_time, items, comments, stories]


download_prod_job = build_assets_job(
    "hacker_news_api_download",
    assets=ASSETS,
    resource_defs={
        **{
            "partition_bounds": partition_bounds,
            "hn_client": hn_api_subsample_client.configured({"sample_rate": 10}),
        },
        **RESOURCES_PROD,
    },
    config=hourly_download_config,
    tags=DOWNLOAD_TAGS,
)


download_staging_job = build_assets_job(
    "hacker_news_api_download",
    assets=ASSETS,
    resource_defs={
        **{
            "partition_bounds": partition_bounds,
            "hn_client": hn_api_subsample_client.configured({"sample_rate": 10}),
        },
        **RESOURCES_STAGING,
    },
    config=hourly_download_config,
    tags=DOWNLOAD_TAGS,
)

download_local_job = build_assets_job(
    "hacker_news_api_download",
    assets=ASSETS,
    resource_defs={
        **{"partition_bounds": partition_bounds, "hn_client": hn_snapshot_client},
        **RESOURCES_LOCAL,
    },
    config=hourly_download_config,
    tags=DOWNLOAD_TAGS,
    executor_def=in_process_executor,
)
