import dagster as dg

weekly_update_schedule = dg.ScheduleDefinition(
    name="analysis_update_job",
    target=dg.AssetSelection.keys("adhoc_request"),
    cron_schedule="0 0 * * 1",  # every Monday at midnight
)
