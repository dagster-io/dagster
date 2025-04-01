from dagster_duckdb import DuckDBResource
from etl_tutorial import assets
from etl_tutorial.schedules import weekly_update_schedule
from etl_tutorial.sensors import adhoc_request_job, adhoc_request_sensor

import dagster as dg

tutorial_assets = dg.load_assets_from_modules([assets])
tutorial_asset_checks = dg.load_asset_checks_from_modules([assets])

defs = dg.Definitions(
    assets=tutorial_assets,
    asset_checks=tutorial_asset_checks,
    schedules=[weekly_update_schedule],
    jobs=[adhoc_request_job],
    sensors=[adhoc_request_sensor],
    resources={"duckdb": DuckDBResource(database="data/mydb.duckdb")},
)
