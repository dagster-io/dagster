from dagster import (
    assets_from_package_module,
    build_assets_job,
    namespaced,
    schedule_from_partitions,
)

from . import assets

core_assets = namespaced("core", assets_from_package_module(assets))

core_assets_schedule = schedule_from_partitions(
    build_assets_job(
        name="core",
        assets=core_assets,
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
)

core_definitions = core_assets + [core_assets_schedule]
