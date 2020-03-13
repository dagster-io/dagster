import datetime
from collections import defaultdict

from dagster import PartitionSetDefinition, ScheduleExecutionContext
from dagster.core.definitions.pipeline import PipelineRunsFilter
from dagster.core.scheduler import SchedulerHandle
from dagster.core.storage.pipeline_run import PipelineRunStatus
from dagster.utils.partitions import date_partition_range


def define_scheduler():
    # Done instead of using schedules to avoid circular dependency issues.
    return SchedulerHandle(schedule_defs=get_bay_bikes_schedules() + get_toys_schedules())


def _fetch_runs_by_partition(instance, partition_set_def):
    # query runs db for this partition set
    filters = PipelineRunsFilter(tags={'dagster/partition_set': partition_set_def.name})
    partition_set_runs = instance.get_runs(filters)

    runs_by_partition = defaultdict(list)

    for run in partition_set_runs:
        runs_by_partition[run.tags['dagster/partition']].append(run)

    return runs_by_partition


def backfilling_partition_selector(
    context: ScheduleExecutionContext, partition_set_def: PartitionSetDefinition
):
    runs_by_partition = _fetch_runs_by_partition(context.instance, partition_set_def)

    selected = None
    for partition in partition_set_def.get_partitions():
        runs = runs_by_partition[partition.name]

        selected = partition

        # break when we find the first empty partition
        if len(runs) == 0:
            break

    # may return an already satisfied final partition - bank on should_execute to prevent firing in schedule
    return selected


def backfill_should_execute(context, partition_set_def):
    runs_by_partition = _fetch_runs_by_partition(context.instance, partition_set_def)
    for runs in runs_by_partition.values():
        for run in runs:
            # if any active runs - don't start a new one
            if run.status == PipelineRunStatus.STARTED:
                return False  # would be nice to return a reason here

    available_partitions = set([partition.name for partition in partition_set_def.get_partitions()])
    satisfied_partitions = set(runs_by_partition.keys())
    return bool(available_partitions.difference(satisfied_partitions))


def backfill_test_schedule():
    # create weekly partition set
    partition_set = PartitionSetDefinition(
        name='unreliable_weekly',
        pipeline_name='unreliable_pipeline',
        partition_fn=date_partition_range(
            # first sunday of the year
            start=datetime.datetime(2020, 1, 5),
            delta=datetime.timedelta(weeks=1),
        ),
        environment_dict_fn_for_partition=lambda _: {'storage': {'filesystem': {}}},
    )

    def _should_execute(context):
        return backfill_should_execute(context, partition_set)

    return partition_set.create_schedule_definition(
        schedule_name='backfill_unreliable_weekly',
        cron_schedule="* * * * *",  # tick every minute
        partition_selector=backfilling_partition_selector,
        should_execute=_should_execute,
    )


def get_bay_bikes_schedules():
    from dagster_examples.bay_bikes.schedules import (
        daily_weather_ingest_schedule,
        monthly_trip_ingest_schedule,
    )

    return [daily_weather_ingest_schedule, monthly_trip_ingest_schedule]


def get_toys_schedules():
    from dagster import ScheduleDefinition, file_relative_path

    return [
        backfill_test_schedule(),
        ScheduleDefinition(
            name="many_events_every_min",
            cron_schedule="* * * * *",
            pipeline_name='many_events',
            environment_dict_fn=lambda _: {"storage": {"filesystem": {}}},
        ),
        ScheduleDefinition(
            name="pandas_hello_world_hourly",
            cron_schedule="0 * * * *",
            pipeline_name="pandas_hello_world_pipeline",
            environment_dict_fn=lambda _: {
                'solids': {
                    'mult_solid': {
                        'inputs': {
                            'num_df': {
                                'csv': {
                                    'path': file_relative_path(
                                        __file__, "pandas_hello_world/data/num.csv"
                                    )
                                }
                            }
                        }
                    },
                    'sum_solid': {
                        'inputs': {
                            'num_df': {
                                'csv': {
                                    'path': file_relative_path(
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
