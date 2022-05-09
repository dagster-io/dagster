from hacker_news_assets.resources import RESOURCES_LOCAL, RESOURCES_PROD, RESOURCES_STAGING

from dagster import AssetGroup, schedule_from_partitions

from . import assets


def core_assets(resource_defs):
    return AssetGroup.from_package_module(
        package_module=assets, resource_defs=resource_defs
    ).prefixed("core")


core_assets_prod = core_assets(resource_defs=RESOURCES_PROD)
core_assets_staging = core_assets(resource_defs=RESOURCES_STAGING)
core_assets_local = core_assets(resource_defs=RESOURCES_LOCAL)

RUN_TAGS = {
    "dagster-k8s/config": {
        "container_config": {
            "resources": {
                "requests": {"cpu": "500m", "memory": "2Gi"},
            }
        },
    }
}

core_assets_schedule_prod = schedule_from_partitions(
    core_assets_prod.build_job(name="core_job", tags=RUN_TAGS)
)

core_assets_schedule_staging = schedule_from_partitions(
    core_assets_staging.build_job(name="core_job", tags=RUN_TAGS)
)

core_assets_schedule_local = schedule_from_partitions(
    core_assets_local.build_job(name="core_job", tags=RUN_TAGS)
)


core_definitions_prod = [core_assets_prod, core_assets_schedule_prod]
core_definitions_staging = [core_assets_staging, core_assets_schedule_staging]
core_definitions_local = [core_assets_local, core_assets_schedule_local]
