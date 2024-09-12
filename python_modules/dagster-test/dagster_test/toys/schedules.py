import datetime

from dagster import build_schedule_from_partitioned_job, schedule
from dagster._core.definitions.run_request import RunRequest
from dagster._core.definitions.schedule_definition import ScheduleEvaluationContext
from dagster._core.definitions.time_window_partitions import (
    daily_partitioned_config,
    hourly_partitioned_config,
    monthly_partitioned_config,
    weekly_partitioned_config,
)
from dagster._utils.partitions import DEFAULT_DATE_FORMAT

from dagster_test.toys.longitudinal import longitudinal
from dagster_test.toys.many_events import many_events
from dagster_test.toys.simple_config import simple_config_job
from dagster_test.toys.unreliable import unreliable


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


@schedule(
    job=many_events,
    cron_schedule="0 0 * * *",
    tags={"dagster/priority": "-1", "some_random_tag": "testing"},
)
def configurable_job_schedule(context: ScheduleEvaluationContext):
    scheduled_date = (
        context.scheduled_execution_time.strftime("%Y-%m-%d")
        if context.scheduled_execution_time
        else datetime.datetime.now().strftime("%Y-%m-%d")
    )
    return RunRequest(
        run_key=None,
        run_config={"ops": {"configurable_op": {"config": {"scheduled_date": scheduled_date}}}},
        tags={"date": scheduled_date, "github_test": "test", "okay_t2": "okay"},
    )


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
    from dagster_test.toys.longitudinal import longitudinal_job

    @daily_partitioned_config(start_date="2020-01-01", timezone=_toys_tz_info())
    def longitudinal_config(start, _end):
        return {
            "ops": {
                op.name: {"config": {"partition": start.strftime(DEFAULT_DATE_FORMAT)}}
                for op in longitudinal_job.nodes
            }
        }

    job_def = longitudinal.to_job(config=longitudinal_config)
    return build_schedule_from_partitioned_job(job_def)


@schedule("* * * * *", job=simple_config_job)
def math_schedule():
    return RunRequest(
        run_key=str(1),
        run_config={"ops": {"the_op": {"config": {"foo": "bar"}}}},
        tags={"fee": "fifofum"},
    )


def get_toys_schedules():
    return [
        unreliable_job_test_schedule(),
        hourly_materialization_schedule(),
        daily_materialization_schedule(),
        weekly_materialization_schedule(),
        monthly_materialization_schedule(),
        longitudinal_schedule(),
        configurable_job_schedule,
        math_schedule,
    ]
