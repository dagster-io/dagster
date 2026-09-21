import dagster as dg

# start_schedule
daily_revenue_job = dg.define_asset_job(
    name="daily_revenue_job",
    selection=dg.AssetSelection.groups("analytics").upstream(),
    tags={"team": "data-engineering"},
)

daily_revenue_schedule = dg.ScheduleDefinition(
    name="daily_revenue_schedule",
    job=daily_revenue_job,
    cron_schedule="0 6 * * *",  # 6 AM daily
    default_status=dg.DefaultScheduleStatus.STOPPED,
)
# end_schedule
