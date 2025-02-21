import dagster as dg


# start_basic_schedule
@dg.job
def my_job(): ...


basic_schedule = dg.ScheduleDefinition(job=my_job, cron_schedule="0 0 * * *")
# end_basic_schedule


@dg.asset
def my_asset():
    return 1


# start_basic_asset_schedule
import dagster as dg

asset_job = dg.define_asset_job(
    "asset_job", dg.AssetSelection.groups("some_asset_group")
)

basic_schedule = dg.ScheduleDefinition(job=asset_job, cron_schedule="0 0 * * *")

# end_basic_asset_schedule


# start_run_config_schedule
@dg.op(config_schema={"scheduled_date": str})
def configurable_op(context: dg.OpExecutionContext):
    context.log.info(context.op_config["scheduled_date"])


@dg.job
def configurable_job():
    configurable_op()


@dg.schedule(job=configurable_job, cron_schedule="0 0 * * *")
def configurable_job_schedule(context: dg.ScheduleEvaluationContext):
    scheduled_date = context.scheduled_execution_time.strftime("%Y-%m-%d")
    return dg.RunRequest(
        run_key=None,
        run_config={
            "ops": {"configurable_op": {"config": {"scheduled_date": scheduled_date}}}
        },
        tags={"date": scheduled_date},
    )


# end_run_config_schedule


# start_timezone
my_timezone_schedule = dg.ScheduleDefinition(
    job=my_job, cron_schedule="0 9 * * *", execution_timezone="America/Los_Angeles"
)

# end_timezone

# start_running_in_code
my_running_schedule = dg.ScheduleDefinition(
    job=my_job,
    cron_schedule="0 9 * * *",
    default_status=dg.DefaultScheduleStatus.RUNNING,
)

# end_running_in_code


# start_schedule_logging
@dg.schedule(job=my_job, cron_schedule="* * * * *")
def logs_then_skips(context):
    context.log.info("Logging from a dg.schedule!")
    return dg.SkipReason("Nothing to do")


# end_schedule_logging
