import dagster as dg

# Definition that will fire an error when it is imported
dg.ScheduleDefinition(cron_schedule="* * * * * * * * * *", job_name="foo")
