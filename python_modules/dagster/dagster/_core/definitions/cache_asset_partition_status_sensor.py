from dagster import AssetSelection, DefaultSensorStatus, SensorDefinition
from typing import Optional


def update_asset_partition_status_cache_sensor(
    asset_selection: AssetSelection,
    name: str = "update_asset_partition_status_cache_sensor",
    minimum_interval_seconds: Optional[int] = None,
    default_status: DefaultSensorStatus = DefaultSensorStatus.RUNNING,
) -> SensorDefinition:
    def sensor_fn(context):

        partitions_defs_by_key = context.repository_def.asset_graph.partitions_defs_by_key

        partitioned_asset_keys = (
            set(
                [
                    asset_key
                    for asset_key, partitions_def in partitions_defs_by_key.items()
                    if partitions_def is not None
                ]
            )
            - context.repository_def.asset_graph.source_asset_keys
        )
        cached_partition_status_by_asset = context.instance.get_cached_partition_status_by_asset(
            partitioned_asset_keys
        )

        cursor = (
            AssetReconciliationCursor.from_serialized(
                context.cursor, context.repository_def.asset_graph
            )
            if context.cursor
            else AssetReconciliationCursor.empty()
        )
        run_requests, updated_cursor = reconcile(
            repository_def=context.repository_def,
            asset_selection=asset_selection,
            instance=context.instance,
            cursor=cursor,
            run_tags=run_tags,
        )

        context.update_cursor(updated_cursor.serialize())
        return run_requests

    return SensorDefinition(
        evaluation_fn=sensor_fn,
        name=name,
        asset_selection=asset_selection,
        minimum_interval_seconds=minimum_interval_seconds,
        default_status=default_status,
    )
