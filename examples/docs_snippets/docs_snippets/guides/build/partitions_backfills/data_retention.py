# ruff: noqa
from datetime import datetime, timedelta
from typing import Iterable

import dagster as dg


# Stub helpers used in the docs examples below; replace with your storage logic.
def process_data_for_partition(partition_key: str) -> None: ...


def delete_partition_data(partition_key: str) -> None: ...


def get_existing_data_partitions() -> set[str]:
    return set()


# start_partitioned_asset
@dg.asset(
    partitions_def=dg.DynamicPartitionsDefinition(name="my_data_partitions"),
)
def my_partitioned_asset(context: dg.AssetExecutionContext):
    partition_key = context.partition_key
    return process_data_for_partition(partition_key)


# end_partitioned_asset


# start_retention_sensor
@dg.sensor(minimum_interval_seconds=86400)  # Daily
def data_retention_sensor(context: dg.SensorEvaluationContext):
    """Delete partition data and keys older than the retention window."""
    retention_days = 90
    cutoff_date = datetime.now() - timedelta(days=retention_days)

    partitions_to_delete = []
    for partition_key in context.instance.get_dynamic_partitions("my_data_partitions"):
        partition_date = datetime.strptime(partition_key, "%Y-%m-%d")
        if partition_date < cutoff_date:
            partitions_to_delete.append(partition_key)

    for partition_key in partitions_to_delete:
        # Your storage-specific deletion (S3, filesystem, database, etc.)
        delete_partition_data(partition_key)
        context.instance.delete_dynamic_partition("my_data_partitions", partition_key)
        context.log.info(f"Deleted partition: {partition_key}")

    return dg.SkipReason(
        f"Processed {len(partitions_to_delete)} partitions for deletion"
    )


# end_retention_sensor


# start_sync_sensor
@dg.sensor(minimum_interval_seconds=3600)  # Hourly
def partition_sync_sensor(context: dg.SensorEvaluationContext):
    """Keep Dagster partitions aligned with actual data."""
    dagster_partitions = set(
        context.instance.get_dynamic_partitions("my_data_partitions")
    )
    actual_partitions = get_existing_data_partitions()  # Scan your storage

    to_add = actual_partitions - dagster_partitions
    for partition_key in to_add:
        context.instance.add_dynamic_partition("my_data_partitions", partition_key)
        context.log.info(f"Added partition: {partition_key}")

    to_remove = dagster_partitions - actual_partitions
    for partition_key in to_remove:
        context.instance.delete_dynamic_partition("my_data_partitions", partition_key)
        context.log.info(f"Removed orphaned partition: {partition_key}")

    return dg.SkipReason(f"Synced partitions: +{len(to_add)}, -{len(to_remove)}")


# end_sync_sensor
