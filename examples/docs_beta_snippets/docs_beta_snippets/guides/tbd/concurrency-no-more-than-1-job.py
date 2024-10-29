import time

import dagster as dg


@dg.asset
def first_asset(context: dg.AssetExecutionContext):
    # sleep so that the asset takes some time to execute
    time.sleep(75)
    context.log.info("First asset executing")


my_job = dg.define_asset_job("my_job", [first_asset])


@dg.schedule(
    job=my_job,
    # Runs every minute to show the effect of the concurrency limit
    cron_schedule="* * * * *",
)
def my_schedule(context):
    # Find runs of the same job that are currently running
    # highlight-start
    run_records = context.instance.get_run_records(
        dg.RunsFilter(job_name="my_job", statuses=[dg.DagsterRunStatus.STARTED])
    )
    # skip a schedule run if another run of the same job is already running
    if len(run_records) > 0:
        return dg.SkipReason(
            "Skipping this run because another run of the same job is already running"
        )
    # highlight-end
    return dg.RunRequest()


defs = dg.Definitions(
    assets=[first_asset],
    jobs=[my_job],
    schedules=[my_schedule],
)
