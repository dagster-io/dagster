from dagster import RunRequest, ScheduleDefinition, ScheduleEvaluationContext, job, op, schedule


# start_basic_schedule
@job
def my_job():
    ...


basic_schedule = ScheduleDefinition(job=my_job, cron_schedule="0 0 * * *")
# end_basic_schedule

# start_run_config_schedule
@op(config_schema={"scheduled_date": str})
def configurable_op(context):
    context.log.info(context.op_config["scheduled_date"])


@job
def configurable_job():
    configurable_op()


@schedule(job=configurable_job, cron_schedule="0 0 * * *")
def configurable_job_schedule(context: ScheduleEvaluationContext):
    scheduled_date = context.scheduled_execution_time.strftime("%Y-%m-%d")
    return RunRequest(
        run_config={"ops": {"configurable_op": {"config": {"scheduled_date": scheduled_date}}}},
        tags={"date": scheduled_date},
    )


# end_run_config_schedule


# start_timezone
my_timezone_schedule = ScheduleDefinition(
    job=my_job, cron_schedule="0 9 * * *", execution_timezone="US/Pacific"
)

# end_timezone
