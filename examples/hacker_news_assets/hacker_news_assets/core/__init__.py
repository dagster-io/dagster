from ..partitions import hourly_partitions
from dagster import AssetGroup, schedule_from_partitions

from . import assets

core_assets = load_assets_from_package({assets}, prefix="core")

RUN_TAGS = {
    "dagster-k8s/config": {
        "container_config": {
            "resources": {
                "requests": {"cpu": "500m", "memory": "2Gi"},
            }
        },
    }
}

core_job_spec = JobSpec(
    selection="core>id_range_for_time++", tags=RUN_TAGS
)  # probably want to do better here

core_assets_schedule = schedule_from_partitions(
    job_name="core_job", partitions_def=hourly_partitions
)
