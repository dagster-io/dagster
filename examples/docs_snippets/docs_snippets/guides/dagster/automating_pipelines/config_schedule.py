from dagster import schedule, ScheduleEvaluationContext, RunRequest

##sets the schedule to be updated everyday at 9:00 AM

@schedule(job=configurable_job, cron_schedule="0 9 * * *")
def configurable_job_schedule(context: ScheduleEvaluationContext):
  if context.scheduled_execution_time.weekday()<5:
    activity_selection='grind'
  else: 
    activity_selection= 'party'
  return RunRequest(
    run_config={"ops": {"configurable_op": {"config": {"activity": activity_selection}}}})