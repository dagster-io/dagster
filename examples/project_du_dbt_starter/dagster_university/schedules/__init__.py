import dagster as dg

from ..jobs import trip_update_job, weekly_update_job

trip_update_schedule = dg.ScheduleDefinition(
    job=trip_update_job,
    cron_schedule="0 0 5 * *",  # every 5th of the month at midnight
)

weekly_update_schedule = dg.ScheduleDefinition(
    job=weekly_update_job,
    cron_schedule="0 0 * * 1",  # every Monday at midnight
)
