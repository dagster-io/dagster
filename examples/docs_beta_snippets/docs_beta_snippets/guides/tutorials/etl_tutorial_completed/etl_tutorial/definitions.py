from dagster_duckdb import DuckDBResource

import dagster as dg

from . import assets
from .schedules import weekly_update_schedule
from .sensors import adhoc_request_job, adhoc_request_sensor

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
