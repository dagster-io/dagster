from dagster import build_assets_job, in_process_executor
from hacker_news_assets.assets.id_range_for_time import id_range_for_time
from hacker_news_assets.assets.items import comments, items, stories
from hacker_news_assets.resources import RESOURCES_LOCAL, RESOURCES_PROD, RESOURCES_STAGING
from hacker_news_assets.resources.hn_resource import hn_api_subsample_client, hn_snapshot_client

DOWNLOAD_TAGS = {
    "dagster-k8s/config": {
        "container_config": {
            "resources": {
                "requests": {"cpu": "500m", "memory": "2Gi"},
            }
        },
    }
}


ASSETS = [id_range_for_time, items, comments, stories]


download_prod_job = build_assets_job(
    "hacker_news_api_download",
    assets=ASSETS,
    resource_defs={
        **{"hn_client": hn_api_subsample_client.configured({"sample_rate": 10})},
        **RESOURCES_PROD,
    },
    tags=DOWNLOAD_TAGS,
)


download_staging_job = build_assets_job(
    "hacker_news_api_download",
    assets=ASSETS,
    resource_defs={
        **{"hn_client": hn_api_subsample_client.configured({"sample_rate": 10})},
        **RESOURCES_STAGING,
    },
    tags=DOWNLOAD_TAGS,
)

download_local_job = build_assets_job(
    "hacker_news_api_download",
    assets=ASSETS,
    resource_defs={**{"hn_client": hn_snapshot_client}, **RESOURCES_LOCAL},
    tags=DOWNLOAD_TAGS,
    executor_def=in_process_executor,
)
