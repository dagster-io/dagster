import dagster as dg

from .assets import my_analytics_asset

regenerate_analytics_job = dg.define_asset_job(
    "regenerate_analytics_job",
    selection=[my_analytics_asset],
)

regenerate_analytics_hourly_schedule = dg.ScheduleDefinition(
    job=regenerate_analytics_job,
    cron_schedule="0 * * * *",
)
