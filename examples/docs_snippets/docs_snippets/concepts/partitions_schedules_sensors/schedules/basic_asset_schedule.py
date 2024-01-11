# ruff: noqa

from dagster import (
    AssetSelection,
    DefaultScheduleStatus,
    Definitions,
    ScheduleDefinition,
    asset,
    define_asset_job,
)

# start_assets
from dagster import asset


@asset(group_name="ecommerce_assets")
def orders_asset():
    return 1


@asset(group_name="ecommerce_assets")
def users_asset():
    return 2


# end_assets

# start_job
from dagster import AssetSelection, define_asset_job


ecommerce_asset_job = define_asset_job(
    "ecommerce_asset_job", AssetSelection.groups("ecommerce_assets")
)

# end_job


# start_schedule
from dagster import ScheduleDefinition


ecommerce_schedule = ScheduleDefinition(
    job=ecommerce_asset_job,
    cron_schedule="15 5 * * 1-5",
    default_status=DefaultScheduleStatus.RUNNING,
)
# end_schedule


# start_definitions

from dagster import Definitions


defs = Definitions(
    assets=[orders_asset, users_asset],
    jobs=[ecommerce_asset_job],
    schedules=[ecommerce_schedule],
)
# end_definitions
