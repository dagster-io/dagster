from dagster import in_process_executor
from dagster.core.asset_defs import build_assets_job
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


from ..asset_collection import asset_collection

download_job = asset_collection.build_asset_job(subset="id_range_for_time*", tags=DOWNLOAD_TAGS)