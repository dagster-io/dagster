from hacker_news_assets.assets import asset_group

download_job = asset_group.build_job(
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
