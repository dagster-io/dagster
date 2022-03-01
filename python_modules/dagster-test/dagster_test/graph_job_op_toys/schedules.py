import datetime

from dagster_test.graph_job_op_toys.longitudinal import longitudinal
from dagster_test.graph_job_op_toys.many_events import many_events
from dagster_test.graph_job_op_toys.unreliable import unreliable

from dagster import build_schedule_from_partitioned_job
from dagster.core.definitions.time_window_partitions import (
    daily_partitioned_config,
    hourly_partitioned_config,
    monthly_partitioned_config,
    weekly_partitioned_config,
)


def _toys_tz_info():
    # Provides execution_timezone information, which is only used to determine execution time when
    # the scheduler configured is the DagsterCommandLineScheduler
    return "US/Pacific"


def unreliable_job_test_schedule():
    @weekly_partitioned_config(start_date="2020-01-05", timezone=_toys_tz_info())
    def unreliable_config(_start, _end):
        return {}

    unreliable_weekly_job = unreliable.to_job(config=unreliable_config)
    unreliable_weekly_schedule = build_schedule_from_partitioned_job(unreliable_weekly_job)

    return unreliable_weekly_schedule


def hourly_materialization_schedule():
    @hourly_partitioned_config(start_date=datetime.datetime(2021, 1, 1), timezone=_toys_tz_info())
    def hourly_materialization_config(_start, _end):
        return {}

    return build_schedule_from_partitioned_job(
        many_events.to_job("many_events_hourly", config=hourly_materialization_config),
    )


def daily_materialization_schedule():
    @daily_partitioned_config(start_date=datetime.datetime(2021, 1, 1), timezone=_toys_tz_info())
    def daily_materialization_config(_start, _end):
        return {}

    return build_schedule_from_partitioned_job(
        many_events.to_job("many_events_daily", config=daily_materialization_config),
    )


def weekly_materialization_schedule():
    @weekly_partitioned_config(start_date=datetime.datetime(2021, 1, 1), timezone=_toys_tz_info())
    def weekly_materialization_config(_start, _end):
        return {}

    return build_schedule_from_partitioned_job(
        many_events.to_job("many_events_weekly", config=weekly_materialization_config),
    )


def monthly_materialization_schedule():
    @monthly_partitioned_config(start_date=datetime.datetime(2021, 1, 1), timezone=_toys_tz_info())
    def monthly_materialization_config(_start, _end):
        return {}

    return build_schedule_from_partitioned_job(
        many_events.to_job("many_events_monthly", config=monthly_materialization_config),
    )


def longitudinal_schedule():
    from .longitudinal import longitudinal_job

    @daily_partitioned_config(start_date="2020-01-01", timezone=_toys_tz_info())
    def longitudinal_config(start, _end):
        return {
            "ops": {
                op.name: {"config": {"partition": start.to_date_string()}}
                for op in longitudinal_job.solids
            }
        }

    longitudinal_job = longitudinal.to_job(config=longitudinal_config)
    return build_schedule_from_partitioned_job(longitudinal_job)


def get_toys_schedules():
    return [
        unreliable_job_test_schedule(),
        hourly_materialization_schedule(),
        daily_materialization_schedule(),
        weekly_materialization_schedule(),
        monthly_materialization_schedule(),
        longitudinal_schedule(),
    ]
