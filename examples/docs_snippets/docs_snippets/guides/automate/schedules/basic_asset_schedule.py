# ruff: noqa

import dagster as dg


# start_assets
@dg.asset(group_name="ecommerce_assets")
def orders_asset():
    return 1


@dg.asset(group_name="ecommerce_assets")
def users_asset():
    return 2


# end_assets

# start_schedule
ecommerce_schedule = dg.ScheduleDefinition(
    name="ecommerce_schedule",
    target=dg.AssetSelection.groups("ecommerce_assets"),
    cron_schedule="15 5 * * 1-5",
    default_status=dg.DefaultScheduleStatus.RUNNING,
)

# end_schedule


# start_definitions
defs = dg.Definitions(
    assets=[orders_asset, users_asset],
    schedules=[ecommerce_schedule],
)
# end_definitions
