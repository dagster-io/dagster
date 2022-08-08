from dagster import In, Out, op, ScheduleDefinition

# Definition that will fire an error when it is imported
ScheduleDefinition(cron_schedule="* * * * * * * * * *", job_name="foo")
