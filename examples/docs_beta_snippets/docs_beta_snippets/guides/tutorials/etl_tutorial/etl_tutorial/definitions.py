import dagster as dg
from dagster_duckdb import DuckDBResource
from .assets import assets
from .sensors import adhoc_request_sensor
from .jobs import analysis_update_job, adhoc_request_job
from .schedules import weekly_update_schedule

all_assets = dg.load_assets_from_modules([assets])

all_asset_checks = dg.load_asset_checks_from_modules([assets])

defs = dg.Definitions(
    assets=all_assets,
    asset_checks=all_asset_checks,
    schedules=[weekly_update_schedule],
    jobs=[analysis_update_job,adhoc_request_job],
    sensors=[adhoc_request_sensor],
    resources={
            "duckdb": DuckDBResource(database="data/mydb.duckdb")  
    }
)
