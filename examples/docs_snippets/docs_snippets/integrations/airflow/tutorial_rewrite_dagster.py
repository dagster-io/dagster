# start_imports
import time
from datetime import datetime, timedelta

from dagster import (
    Definitions,
    In,
    Nothing,
    OpExecutionContext,
    RetryPolicy,
    ScheduleDefinition,
    job,
    op,
    schedule,
)


# start_ops
@op
def print_date(context: OpExecutionContext) -> datetime:
    ds = datetime.now()
    context.log.info(ds)
    return ds


@op(retry_policy=RetryPolicy(max_retries=3), ins={"start": In(Nothing)})
def sleep():
    time.sleep(5)


@op
def templated(context: OpExecutionContext, ds: datetime):
    for _i in range(5):
        context.log.info(ds)
        context.log.info(ds - timedelta(days=7))


# end_ops


# start_job
@job(tags={"dagster/max_retries": 1, "dag_name": "example"})
def tutorial_job():
    ds = print_date()
    sleep(ds)
    templated(ds)


# end_job

# start_schedule
schedule = ScheduleDefinition(job=tutorial_job, cron_schedule="@daily")
# end_schedule


# start_repo
defs = Definitions(
    jobs=[tutorial_job],
    schedules=[schedule],
)
# end_repo
