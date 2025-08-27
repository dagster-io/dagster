import dagster as dg

# start_basic_schedule
basic_schedule = dg.ScheduleDefinition(
    name="basic_schedule", cron_schedule="0 0 * * *", target="*"
)
# end_basic_schedule


@dg.asset
def my_asset():
    return 1


# start_basic_asset_schedule
import dagster as dg

basic_schedule = dg.ScheduleDefinition(
    name="basic_asset_schedule",
    cron_schedule="0 0 * * *",
    target=dg.AssetSelection.groups("some_asset_group"),
)

# end_basic_asset_schedule


# start_run_config_schedule
import dagster as dg


class AssetConfig(dg.Config):
    scheduled_date: str


@dg.asset
def configurable_asset(context: dg.AssetExecutionContext, config: AssetConfig):
    context.log.info(config.scheduled_date)


@dg.schedule(target=configurable_asset, cron_schedule="0 0 * * *")
def configurable_job_schedule(context: dg.ScheduleEvaluationContext):
    scheduled_date = context.scheduled_execution_time.strftime("%Y-%m-%d")
    return dg.RunRequest(
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
my_timezone_schedule = dg.ScheduleDefinition(
    name="my_timezone_schedule",
    target="*",
    cron_schedule="0 9 * * *",
    execution_timezone="America/Los_Angeles",
)

# end_timezone

# start_running_in_code
my_running_schedule = dg.ScheduleDefinition(
    name="my_running_schedule",
    target="*",
    cron_schedule="0 9 * * *",
    default_status=dg.DefaultScheduleStatus.RUNNING,
)

# end_running_in_code


# start_schedule_logging
@dg.schedule(target="*", cron_schedule="* * * * *")
def logs_then_skips(context):
    context.log.info("Logging from a dg.schedule!")
    return dg.SkipReason("Nothing to do")


# end_schedule_logging
