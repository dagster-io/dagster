# start_imports
import time
from datetime import date, timedelta

from dagster import (
    RetryPolicy,
    RunRequest,
    ScheduleDefinition,
    ScheduleEvaluationContext,
    job,
    op,
    repository,
    schedule,
)


# start_ops
@op
def print_date():
    dt = date.today()
    print(dt)
    return dt

@op(
    retry_policy=RetryPolicy(
        max_retries=3
    )
)
def sleep(dt: date):
    time.sleep(5)

@op
def templated(dt: date):
    for i in range(5):
        print(dt)
        print(dt - timedelta(days=7))
# end_ops

# start_job
@job(tags={"dagster/max_retries": 1, "dag_name": "example"})
def tutorial_job():
    dt = print_date()
    sleep(dt)
    templated(dt)
# end_job

# start_basic_schedule
schedule = ScheduleDefinition(job=tutorial_job, cron_schedule="@daily")
# end_basic_schedule


# start_schedule
@schedule(job=tutorial_job, cron_schedule="@daily")
def tutorial_job_schedule(context: ScheduleEvaluationContext):
    scheduled_date = context.scheduled_execution_time.strftime("%Y-%m-%d")
    return RunRequest(
        run_key=None,
        run_config={
            "ops": {"configurable_op": {"config": {"scheduled_date": scheduled_date}}}
        },
        tags={"date": scheduled_date},
    )
# end_schedule

# start_repo
@repository
def rewrite_repo():
    return [tutorial_job, tutorial_job_schedule, schedule]
# end_repo