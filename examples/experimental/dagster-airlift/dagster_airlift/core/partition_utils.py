from typing import Callable

from dagster import (
    AssetKey,
    PartitionsDefinition,
    TimeWindowPartitionsDefinition,
    _check as check,
)
from dagster._time import get_timezone

from dagster_airlift.core.airflow_instance import TaskInstance


def default_partition_key_from_task_instance(
    partitions_def: PartitionsDefinition, task_instance: TaskInstance, asset_key: AssetKey
) -> str:
    partitions_def = check.inst(
        partitions_def,
        TimeWindowPartitionsDefinition,
        "Only time window-partitioned assets are supported.",
    )
    logical_date = task_instance.logical_datetime
    logical_date_timezone = logical_date.tzinfo
    partitions_def_timezone = get_timezone(partitions_def.timezone)
    check.invariant(
        logical_date_timezone == partitions_def_timezone,
        (
            f"The timezone of the retrieved logical date from the airflow run ({logical_date_timezone}) does not "
            f"match that of the partitions definition ({partitions_def_timezone}) for asset key {asset_key.to_user_string()}."
            "To ensure consistent behavior, the timezone of the logical date must match the timezone of the partitions definition."
        ),
    )
    # Assuming that "logical_date" lies on a partition, the previous partition window
    # (where upper bound can be the passed-in date, which is why we set respect_bounds=False)
    # will end on the logical date. This would indicate that there is a partition for the logical date.
    partition_window = check.not_none(
        partitions_def.get_prev_partition_window(logical_date, respect_bounds=False),
        f"Could not find partition for logical date {logical_date.isoformat()}. This likely means that your partition range is too small to cover the logical date.",
    )
    check.invariant(
        logical_date.timestamp() == partition_window.end.timestamp(),
        (
            "Expected logical date to match a partition in the partitions definition. This likely means that "
            "The partition range is not aligned with the scheduling interval in airflow."
        ),
    )
    check.invariant(
        logical_date.timestamp() >= partitions_def.start.timestamp(),
        (
            f"For run {task_instance.run_id} in dag {task_instance.dag_id}, "
            f"Logical date is before the start of the partitions definition in asset key {asset_key.to_user_string()}. "
            "Ensure that the start date of your PartitionsDefinition is early enough to capture current runs coming from airflow."
        ),
    )
    return partitions_def.get_partition_key_for_timestamp(logical_date.timestamp())


PartitionResolverFn = Callable[[PartitionsDefinition, TaskInstance, AssetKey], str]
