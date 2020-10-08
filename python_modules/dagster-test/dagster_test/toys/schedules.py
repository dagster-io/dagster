import datetime
from collections import defaultdict

from dagster import PartitionSetDefinition, ScheduleExecutionContext
from dagster.core.storage.pipeline_run import PipelineRunStatus, PipelineRunsFilter
from dagster.utils.partitions import date_partition_range


def _fetch_runs_by_partition(instance, partition_set_def, status_filters=None):
    # query runs db for this partition set
    filters = PipelineRunsFilter(tags={"dagster/partition_set": partition_set_def.name})
    partition_set_runs = instance.get_runs(filters)

    runs_by_partition = defaultdict(list)

    for run in partition_set_runs:
        if not status_filters or run.status in status_filters:
            runs_by_partition[run.tags["dagster/partition"]].append(run)

    return runs_by_partition


def backfilling_partition_selector(
    context: ScheduleExecutionContext, partition_set_def: PartitionSetDefinition, retry_failed=False
):
    status_filters = [PipelineRunStatus.SUCCESS] if retry_failed else None
    runs_by_partition = _fetch_runs_by_partition(
        context.instance, partition_set_def, status_filters
    )

    selected = None
    for partition in partition_set_def.get_partitions():
        runs = runs_by_partition[partition.name]

        selected = partition

        # break when we find the first empty partition
        if len(runs) == 0:
            break

    # may return an already satisfied final partition - bank on should_execute to prevent firing in schedule
    return selected


def backfill_should_execute(context, partition_set_def, retry_failed=False):
    status_filters = (
        [PipelineRunStatus.STARTED, PipelineRunStatus.SUCCESS] if retry_failed else None
    )
    runs_by_partition = _fetch_runs_by_partition(
        context.instance, partition_set_def, status_filters
    )
    for runs in runs_by_partition.values():
        for run in runs:
            # if any active runs - don't start a new one
            if run.status == PipelineRunStatus.STARTED:
                return False  # would be nice to return a reason here

    available_partitions = set([partition.name for partition in partition_set_def.get_partitions()])
    satisfied_partitions = set(runs_by_partition.keys())
    is_remaining_partitions = bool(available_partitions.difference(satisfied_partitions))
    return is_remaining_partitions


def backfill_test_schedule():
    schedule_name = "backfill_unreliable_weekly"
    # create weekly partition set
    partition_set = PartitionSetDefinition(
        name="unreliable_weekly",
        pipeline_name="unreliable_pipeline",
        partition_fn=date_partition_range(
            # first sunday of the year
            start=datetime.datetime(2020, 1, 5),
            delta=datetime.timedelta(weeks=1),
        ),
        run_config_fn_for_partition=lambda _: {"storage": {"filesystem": {}}},
    )

    def _should_execute(context):
        return backfill_should_execute(context, partition_set)

    return partition_set.create_schedule_definition(
        schedule_name=schedule_name,
        cron_schedule="* * * * *",  # tick every minute
        partition_selector=backfilling_partition_selector,
        should_execute=_should_execute,
    )


def materialization_schedule():
    # create weekly partition set
    schedule_name = "many_events_partitioned"
    partition_set = PartitionSetDefinition(
        name="many_events_minutely",
        pipeline_name="many_events",
        partition_fn=date_partition_range(start=datetime.datetime(2020, 1, 1)),
        run_config_fn_for_partition=lambda _: {"storage": {"filesystem": {}}},
    )

    def _should_execute(context):
        return backfill_should_execute(context, partition_set)

    return partition_set.create_schedule_definition(
        schedule_name=schedule_name,
        cron_schedule="* * * * *",  # tick every minute
        partition_selector=backfilling_partition_selector,
        should_execute=_should_execute,
    )


def longitudinal_schedule():
    from .longitudinal import longitudinal_config

    schedule_name = "longitudinal_demo"

    partition_set = PartitionSetDefinition(
        name="ingest_and_train",
        pipeline_name="longitudinal_pipeline",
        partition_fn=date_partition_range(start=datetime.datetime(2020, 1, 1)),
        run_config_fn_for_partition=longitudinal_config,
    )

    def _should_execute(context):
        return backfill_should_execute(context, partition_set, retry_failed=True)

    def _partition_selector(context, partition_set):
        return backfilling_partition_selector(context, partition_set, retry_failed=True)

    return partition_set.create_schedule_definition(
        schedule_name=schedule_name,
        cron_schedule="*/5 * * * *",  # tick every 5 minutes
        partition_selector=_partition_selector,
        should_execute=_should_execute,
    )


def get_toys_schedules():
    from dagster import ScheduleDefinition, file_relative_path

    return [
        backfill_test_schedule(),
        longitudinal_schedule(),
        materialization_schedule(),
        ScheduleDefinition(
            name="many_events_every_min",
            cron_schedule="* * * * *",
            pipeline_name="many_events",
            run_config_fn=lambda _: {"storage": {"filesystem": {}}},
        ),
        ScheduleDefinition(
            name="pandas_hello_world_hourly",
            cron_schedule="0 * * * *",
            pipeline_name="pandas_hello_world_pipeline",
            run_config_fn=lambda _: {
                "solids": {
                    "mult_solid": {
                        "inputs": {
                            "num_df": {
                                "csv": {
                                    "path": file_relative_path(
                                        __file__, "pandas_hello_world/data/num.csv"
                                    )
                                }
                            }
                        }
                    },
                    "sum_solid": {
                        "inputs": {
                            "num_df": {
                                "csv": {
                                    "path": file_relative_path(
                                        __file__, "pandas_hello_world/data/num.csv"
                                    )
                                }
                            }
                        }
                    },
                },
                "storage": {"filesystem": {}},
            },
        ),
    ]
