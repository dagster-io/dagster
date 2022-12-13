# start_imports
import time
from datetime import datetime, timedelta

from dagster import (
    In,
    Nothing,
    RetryPolicy,
    RunRequest,
    ScheduleEvaluationContext,
    job,
    op,
    repository,
    schedule,
)


# start_ops
@op
def print_date(context) -> datetime:
    ds = datetime.fromisoformat(context.get_tag("date"))
    context.log.info(ds)
    return ds

@op(
    retry_policy=RetryPolicy(
        max_retries=3
    ),
    ins={"start": In(Nothing)}
)
def sleep():
    time.sleep(5)

@op
def templated(context, ds: datetime):
    for i in range(5):
        context.log.info(ds)
        context.log.info(ds - timedelta(days=7))
# end_ops

# start_job
@job(tags={"dagster/max_retries": 1, "dag_name": "example"})
def tutorial_job():
    dt = print_date()
    sleep(dt)
    templated(dt)
# end_job

# start_schedule
@schedule(job=tutorial_job, cron_schedule="@daily")
def schedule(context: ScheduleEvaluationContext):
    scheduled_date = context.scheduled_execution_time
    return RunRequest(
        run_key=None,
        tags={"date": scheduled_date.isoformat()},
    )
# end_schedule

# start_repo
@repository
def rewrite_repo():
    return [tutorial_job, schedule]
# end_repo