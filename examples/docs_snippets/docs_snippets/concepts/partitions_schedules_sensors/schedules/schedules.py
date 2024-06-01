from dagster import (
    DefaultScheduleStatus,
    OpExecutionContext,
    RunRequest,
    ScheduleDefinition,
    ScheduleEvaluationContext,
    SkipReason,
    asset,
    job,
    op,
    schedule,
)


@asset
def my_asset():
    return 1


# start_basic_asset_schedule
from dagster import AssetSelection, ScheduleDefinition, define_asset_job

asset_job = define_asset_job("asset_job", AssetSelection.groups("some_asset_group"))

basic_schedule = ScheduleDefinition(job=asset_job, cron_schedule="0 0 * * *")

# end_basic_asset_schedule


# start_run_config_schedule
@asset(config_schema={"scheduled_date": str})
def configurable_asset(context: OpExecutionContext):
    context.log.info(context.op_config["scheduled_date"])


configurable_job = define_asset_job("configurable_job", [configurable_asset])


@schedule(job=configurable_job, cron_schedule="0 0 * * *")
def configurable_job_schedule(context: ScheduleEvaluationContext):
    scheduled_date = context.scheduled_execution_time.strftime("%Y-%m-%d")
    return RunRequest(
        run_key=None,
        run_config={
            "ops": {
                "configurable_asset": {"config": {"scheduled_date": scheduled_date}}
            }
        },
        tags={"date": scheduled_date},
    )


# end_run_config_schedule


# start_timezone
my_timezone_schedule = ScheduleDefinition(
    job=asset_job, cron_schedule="0 9 * * *", execution_timezone="America/Los_Angeles"
)

# end_timezone

# start_running_in_code
my_running_schedule = ScheduleDefinition(
    job=asset_job,
    cron_schedule="0 9 * * *",
    default_status=DefaultScheduleStatus.RUNNING,
)

# end_running_in_code


# start_schedule_logging
@schedule(job=asset_job, cron_schedule="* * * * *")
def logs_then_skips(context):
    context.log.info("Logging from a schedule!")
    return SkipReason("Nothing to do")


# end_schedule_logging
