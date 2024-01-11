from dagster import asset


@asset(group_name="ecommerce_assets")
def orders_data():
    return 1


@asset(group_name="ecommerce_assets")
def users_data():
    return 2


# start_job
# jobs.py

from dagster import AssetSelection, define_asset_job


ecommerce_asset_job = define_asset_job(
    "ecommerce_asset_job", AssetSelection.groups("ecommerce_assets")
)

# end_job


# start_schedule
# schedules.py

from dagster import ScheduleDefinition
from jobs import ecommerce_asset_job


ecommerce_schedule = ScheduleDefinition(
    job=ecommerce_asset_job,
    cron_schedule="15 5 * * 1-5",
    default_status=DefaultScheduleStatus.RUNNING,
)
# end_schedule


# start_definitions
# __init__.py

from dagster import Definitions
from assets import orders_asset, users_asset
from jobs import ecommerce_asset_job
from schedules import ecommerce_schedule


defs = Definitions(
    assets=[orders_asset, users_asset],
    jobs=[ecommerce_asset_job],
    schedules=[ecommerce_schedule],
)
# end_definitions
