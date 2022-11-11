from quickstart_basic_etl.assets import all_assets

from dagster import ScheduleDefinition, define_asset_job, repository

daily_metrics_report_schedule = ScheduleDefinition(
    job=define_asset_job(name="metrics_report_job"), cron_schedule="0 0 * * *"
)


@repository
def quickstart_basic_etl():
    return [
        all_assets,
        daily_metrics_report_schedule,
    ]
