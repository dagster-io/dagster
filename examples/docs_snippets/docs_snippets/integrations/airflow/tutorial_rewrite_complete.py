# start_example
import time
from datetime import datetime, timedelta

from dagster import (
    In,
    Nothing,
    RetryPolicy,
    ScheduleDefinition,
    job,
    op,
    repository,
    schedule,
)


@op
def print_date(context) -> datetime:
    ds = datetime.now()
    context.log.info(ds)
    return ds


@op(retry_policy=RetryPolicy(max_retries=3), ins={"start": In(Nothing)})
def sleep():
    time.sleep(5)


@op
def templated(context, ds: datetime):
    for _i in range(5):
        context.log.info(ds)
        context.log.info(ds - timedelta(days=7))


@job(tags={"dagster/max_retries": 1, "dag_name": "example"})
def tutorial_job():
    ds = print_date()
    sleep(ds)
    templated(ds)


schedule = ScheduleDefinition(job=tutorial_job, cron_schedule="@daily")


@repository
def rewrite_repo():
    return [tutorial_job, schedule]


# end_example
