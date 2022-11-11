from dagster import (
    ScheduleDefinition,
    define_asset_job,
    load_assets_from_package_module,
    repository,
)

from . import assets

daily_metrics_report_schedule = ScheduleDefinition(
    job=define_asset_job(name="metrics_report_job"), cron_schedule="0 0 * * *"
)


@repository
def quickstart_etl_gcp():
    return [
        load_assets_from_package_module(assets),
        daily_metrics_report_schedule,
    ]
