from hacker_news_assets.partitions import hourly_partitions

from dagster import (
    AssetSelection,
    build_schedule_from_partitioned_job,
    define_asset_job,
    load_assets_from_package_module,
)

from . import assets

CORE = "core"

core_assets = load_assets_from_package_module(package_module=assets, group_name=CORE)

RUN_TAGS = {
    "dagster-k8s/config": {
        "container_config": {
            "resources": {
                "requests": {"cpu": "500m", "memory": "2Gi"},
            }
        },
    }
}

core_assets_schedule = build_schedule_from_partitioned_job(
    define_asset_job(
        "core_job",
        selection=AssetSelection.groups(CORE),
        tags=RUN_TAGS,
        partitions_def=hourly_partitions,
    )
)
