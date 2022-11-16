from dagster import (
    ScheduleDefinition,
    define_asset_job,
    load_assets_from_package_module,
    repository,
)

from . import assets

daily_refresh_schedule = ScheduleDefinition(
    job=define_asset_job(name="all_assets_job"), cron_schedule="0 0 * * *"
)


@repository
def quickstart_etl():
    return [
        load_assets_from_package_module(assets),
        daily_refresh_schedule,
    ]
