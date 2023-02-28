from dagster import schedule, ScheduleEvaluationContext, RunRequest, op, job, build_schedule_context, validate_run_config
import datetime 

@op(config_schema={'activity_selection':str})
def configurable_op(context):
   return activity_selection
@job
def configurable_job():
    configurable_op()


# config_schedule_start
##sets the schedule to be updated everyday at 9:00 AM
@schedule(job=configurable_job, cron_schedule="0 9 * * *")
def configurable_job_schedule(context: ScheduleEvaluationContext):
  if context.scheduled_execution_time.weekday()<5:
    activity_selection='grind'
  else: 
    activity_selection= 'party'
  return RunRequest(
    run_config={"ops": {"configurable_op": {"config": {"activity": activity_selection}}}})

# config_schedule_end

def test_configurable_job_schedule():

    context = build_schedule_context(
      scheduled_execution_time=datetime.datetime(2023, 1, 1))
    if context.scheduled_execution_time.weekday()<5:
      activity_selection='grind'
    else: 
      activity_selection= 'party'
    assert validate_run_config(configurable_job, run_config={"ops": {"configurable_op": {"config": {"activity_selection": activity_selection}}}})

