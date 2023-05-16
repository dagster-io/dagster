import os

from dagster import (
    Definitions,
    ScheduleDefinition,
    define_asset_job,
    load_assets_from_modules,
)

from . import assets, resources

ENV = os.getenv("DAGSTER_ENV", "LOCAL")


daily_schedule = ScheduleDefinition(
    job=define_asset_job(name="dagster_pypi_job"),
    cron_schedule="0 0 * * *",
)

all_assets = load_assets_from_modules([assets])

print("Loading definitions for environment: ", ENV)

defs = Definitions(
    assets=all_assets,
    schedules=[daily_schedule],
    resources=resources.resource_def[ENV.upper()],
)
