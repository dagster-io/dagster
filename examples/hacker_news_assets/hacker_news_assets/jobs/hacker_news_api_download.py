from hacker_news_assets.assets import local_assets, prod_assets, staging_assets

from dagster import AssetGroup, JobDefinition


def make_download_job(asset_group: AssetGroup) -> JobDefinition:
    return asset_group.build_job(
        name="hacker_news_api_download",
        selection=["*comments", "*stories"],
        tags={
            "dagster-k8s/config": {
                "container_config": {
                    "resources": {
                        "requests": {"cpu": "500m", "memory": "2Gi"},
                    }
                },
            }
        },
    )


download_prod_job = make_download_job(prod_assets)
download_staging_job = make_download_job(staging_assets)
download_local_job = make_download_job(local_assets)
