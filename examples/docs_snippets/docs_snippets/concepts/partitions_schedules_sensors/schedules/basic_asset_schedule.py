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
@asset(group_name="ecommerce_assets")
def orders_asset():
    return 1


@asset(group_name="ecommerce_assets")
def users_asset():
    return 2


# end_assets

# start_schedule
ecommerce_schedule = ScheduleDefinition(
    name="ecommerce_schedule",
    target=AssetSelection.groups("ecommerce_assets"),
    cron_schedule="15 5 * * 1-5",
    default_status=DefaultScheduleStatus.RUNNING,
)

# end_schedule


# start_definitions
defs = Definitions(
    assets=[orders_asset, users_asset],
    schedules=[ecommerce_schedule],
)
# end_definitions
