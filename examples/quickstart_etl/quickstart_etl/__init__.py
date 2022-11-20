from dagster import (
    Definitions,
    ScheduleDefinition,
    define_asset_job,
    load_assets_from_package_module,
)

from . import assets

def dagster_defs():
    return Definitions(
        assets=load_assets_from_package_module(assets),
        schedules=[
            ScheduleDefinition(job=define_asset_job(name="all_assets_job"), cron_schedule="0 0 * * *")
        ],
    )
