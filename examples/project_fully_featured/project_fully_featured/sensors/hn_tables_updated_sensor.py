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


def make_hn_tables_updated_multi_asset_sensor(job) -> MultiAssetSensorDefinition:
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


def make_hn_tables_updated_sensor(job) -> SensorDefinition:
    @sensor(name=f"{job.name}_on_hn_tables_updated", job=job)
    def hn_tables_updated_sensor(context):
        cursor_dict = json.loads(context.cursor) if context.cursor else {}
        comments_cursor = cursor_dict.get("comments")
        stories_cursor = cursor_dict.get("stories")

        comments_event_records = context.instance.get_event_records(
            EventRecordsFilter(
                event_type=DagsterEventType.ASSET_MATERIALIZATION,
                asset_key=AssetKey(["snowflake", "core", "comments"]),
                after_cursor=comments_cursor,
            ),
            ascending=False,
            limit=1,
        )
        stories_event_records = context.instance.get_event_records(
            EventRecordsFilter(
                event_type=DagsterEventType.ASSET_MATERIALIZATION,
                asset_key=AssetKey(["snowflake", "core", "stories"]),
                after_cursor=stories_cursor,
            ),
            ascending=False,
            limit=1,
        )

        if not comments_event_records or not stories_event_records:
            return

        # make sure we only generate events if both table_a and table_b have been materialized since
        # the last evaluation.
        yield RunRequest(run_key=None)

        # update the sensor cursor by combining the individual event cursors from the two separate
        # asset event streams
        context.update_cursor(
            json.dumps(
                {
                    "comments": comments_event_records[0].storage_id,
                    "stories": stories_event_records[0].storage_id,
                }
            )
        )

    return hn_tables_updated_sensor
