from dagster import SkipReason, DefaultSensorStatus, SensorDefinition
from typing import Optional
from dagster._core.storage.partition_status_cache import update_asset_status_cache_values


def update_asset_partition_status_cache_sensor(
    name: str = "__dagster_asset_partition_status_cache_sensor",
    minimum_interval_seconds: Optional[int] = None,
    default_status: DefaultSensorStatus = DefaultSensorStatus.RUNNING,
) -> SensorDefinition:
    def sensor_fn(context):
        update_asset_status_cache_values(context.instance, context.repository_def.asset_graph)
        return SkipReason("No runs are requested from this sensor")

    return SensorDefinition(
        evaluation_fn=sensor_fn,
        name=name,
        minimum_interval_seconds=minimum_interval_seconds,
        default_status=default_status,
    )
