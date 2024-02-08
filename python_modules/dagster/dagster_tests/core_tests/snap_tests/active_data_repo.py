from datetime import datetime

from dagster import daily_partitioned_config, job, op, repository
from dagster._core.definitions.decorators.schedule_decorator import schedule


@op
def foo_op(_):
    pass


@schedule(
    cron_schedule="@daily",
    job_name="foo_job",
    execution_timezone="US/Central",
)
def foo_schedule():
    return {}


@daily_partitioned_config(start_date=datetime(2020, 1, 1), minute_offset=15)
def my_partitioned_config(_start: datetime, _end: datetime):
    return {}


@job(config=my_partitioned_config)
def foo_job():
    foo_op()


@repository
def a_repo():
    return [foo_job]
