import dagster as dg


@dg.op(config_schema={"activity_selection": str})
def configurable_op(context: dg.OpExecutionContext):
    pass


@dg.job
def configurable_job():
    configurable_op()


# config_schedule_start
# sets the dg.schedule to be updated everyday at 9:00 AM
@dg.schedule(job=configurable_job, cron_schedule="0 9 * * *")
def configurable_job_schedule(context: dg.ScheduleEvaluationContext):
    if context.scheduled_execution_time.weekday() < 5:
        activity_selection = "grind"
    else:
        activity_selection = "party"
    return dg.RunRequest(
        run_config={
            "ops": {"configurable_op": {"config": {"activity": activity_selection}}}
        }
    )


# config_schedule_end
