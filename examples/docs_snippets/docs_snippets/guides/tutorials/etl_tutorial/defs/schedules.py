import dagster as dg

weekly_update_schedule = dg.ScheduleDefinition(
    name="analysis_update_job",
    target=dg.AssetSelection.keys("joined_data").upstream(),
    cron_schedule="0 0 * * 1",  # every Monday at midnight
)
