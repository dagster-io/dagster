# start_example
import time
from datetime import datetime, timedelta

import dagster as dg


@dg.op
def print_date(context: dg.OpExecutionContext) -> datetime:
    ds = datetime.now()
    context.log.info(ds)
    return ds


@dg.op(retry_policy=dg.RetryPolicy(max_retries=3), ins={"start": dg.In(dg.Nothing)})
def sleep():
    time.sleep(5)


@dg.op
def templated(context: dg.OpExecutionContext, ds: datetime):
    for _i in range(5):
        context.log.info(ds)
        context.log.info(ds - timedelta(days=7))


@dg.job(tags={"dagster/max_retries": 1, "dag_name": "example"})
def tutorial_job():
    ds = print_date()
    sleep(ds)
    templated(ds)


dg.schedule = dg.ScheduleDefinition(job=tutorial_job, cron_schedule="@daily")


defs = dg.Definitions(
    jobs=[tutorial_job],
    schedules=[dg.schedule],
)


# end_example
