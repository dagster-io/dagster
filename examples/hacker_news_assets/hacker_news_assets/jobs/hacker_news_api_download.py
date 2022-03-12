from dagster import AssetGroup, JobDefinition


def build_download_job(asset_group: AssetGroup) -> JobDefinition:
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
