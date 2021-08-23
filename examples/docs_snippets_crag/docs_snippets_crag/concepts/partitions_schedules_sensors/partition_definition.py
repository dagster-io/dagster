"""isort:skip_file"""
from typing import List, Union

from dagster import (
    Partition,
    PartitionSetDefinition,
    ScheduleEvaluationContext,
    pipeline,
    repository,
    solid,
)


# start_def
def get_date_partitions():
    """Every day in the month of May, 2020"""
    return [Partition(f"2020-05-{str(day).zfill(2)}") for day in range(1, 32)]


def run_config_for_date_partition(partition):
    date = partition.value
    return {"solids": {"process_data_for_date": {"config": {"date": date}}}}


date_partition_set = PartitionSetDefinition(
    name="date_partition_set",
    pipeline_name="my_data_pipeline",
    partition_fn=get_date_partitions,
    run_config_fn_for_partition=run_config_for_date_partition,
)
# end_def


@solid(config_schema={"date": str})
def process_data_for_date(_):
    pass


@pipeline
def my_data_pipeline():
    process_data_for_date()


# start_test_partition_set
from dagster import validate_run_config


def test_my_partition_set():
    for partition in date_partition_set.get_partitions():
        run_config = date_partition_set.run_config_for_partition(partition)
        assert validate_run_config(my_data_pipeline, run_config)


# end_test_partition_set

# start_repo_include
@repository
def my_repository():
    return [
        my_data_pipeline,
        date_partition_set,
    ]


# end_repo_include


def _weekday_run_config_for_partition(partition):
    return {"solids": {"process_data_for_date": {"config": {"date": partition.value}}}}


# start_manual_partition_schedule
weekday_partition_set = PartitionSetDefinition(
    name="weekday_partition_set",
    pipeline_name="my_data_pipeline",
    partition_fn=lambda: [
        Partition("Monday"),
        Partition("Tuesday"),
        Partition("Wednesday"),
        Partition("Thursday"),
        Partition("Friday"),
        Partition("Saturday"),
        Partition("Sunday"),
    ],
    run_config_fn_for_partition=_weekday_run_config_for_partition,
)


def weekday_partition_selector(
    ctx: ScheduleEvaluationContext, partition_set: PartitionSetDefinition
) -> Union[Partition, List[Partition]]:
    """Maps a schedule execution time to the corresponding partition or list of partitions that
    should be executed at that time"""
    partitions = partition_set.get_partitions(ctx.scheduled_execution_time)
    weekday = ctx.scheduled_execution_time.weekday() if ctx.scheduled_execution_time else 0
    return partitions[weekday]


my_schedule = weekday_partition_set.create_schedule_definition(
    "my_schedule",
    "5 0 * * *",
    partition_selector=weekday_partition_selector,
    execution_timezone="US/Eastern",
)


@repository
def my_repository_with_partitioned_schedule():
    return [
        my_data_pipeline,
        weekday_partition_set,
        my_schedule,
    ]


# end_manual_partition_schedule
