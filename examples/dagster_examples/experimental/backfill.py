from dagster_examples.experimental.repo import daily_rollup_schedule

from dagster import execute_partition_set
from dagster.core.instance import DagsterInstance


def select_weekday_partitions(candidate_partitions):
    SATURDAY = 5
    SUNDAY = 6
    return [
        partition
        for partition in candidate_partitions
        if partition.value.weekday() != SATURDAY and partition.value.weekday() != SUNDAY
    ]


partition_set = daily_rollup_schedule.get_partition_set()
execute_partition_set(partition_set, select_weekday_partitions, instance=DagsterInstance.get())
