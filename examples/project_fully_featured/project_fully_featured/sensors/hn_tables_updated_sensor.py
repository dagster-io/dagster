import json

from dagster import (
    AssetKey,
    DagsterEventType,
    EventRecordsFilter,
    RunRequest,
    SensorDefinition,
    sensor,
    multi_asset_sensor,
    MultiAssetSensorDefinition,
)
from dagster._core.definitions.decorators.sensor_decorator import multi_asset_sensor


def make_hn_tables_updated_sensor(job) -> MultiAssetSensorDefinition:
    """
    Returns a sensor that launches the given job when the HN "comments" and "stories" tables have
    both been updated.
    """

    @multi_asset_sensor(
        name=f"{job.name}_on_hn_tables_updated",
        asset_keys=[
            AssetKey(["snowflake", "core", "comments"]),
            AssetKey(["snowflake", "core", "stories"]),
        ],
        job=job,
    )
    def hn_tables_updated_sensor(context):
        materialization_records_by_key = context.latest_materialization_records_by_key()
        if all(materialization_records_by_key.values()):
            yield RunRequest(run_key=None)
            context.advance_cursor(materialization_records_by_key)

    return hn_tables_updated_sensor
