from dagster import (
    Definitions,
    ScheduleDefinition,
    define_asset_job,
    load_assets_from_package_module,
)
from dagster._core.definitions.asset_check_factories.freshness_checks.sensor import (
    build_sensor_for_freshness_checks,
)
from dagster_airbyte import AirbyteResource

from . import assets
from .assets.forecasting import freshness_checks
from .db_io_manager import DbIOManager
from .utils.constants import AIRBYTE_CONFIG, POSTGRES_CONFIG, dbt_resource

# The freshness check sensor will run our freshness checks even if the underlying asset fails to run, for whatever reason.
freshness_check_sensor = build_sensor_for_freshness_checks(freshness_checks=freshness_checks)

defs = Definitions(
    assets=load_assets_from_package_module(assets),
    resources={
        "airbyte": AirbyteResource(**AIRBYTE_CONFIG),
        "dbt": dbt_resource,
        "db_io_manager": DbIOManager(**POSTGRES_CONFIG),
    },
    asset_checks=freshness_checks,
    schedules=[
        # update all assets once a day
        ScheduleDefinition(
            job=define_asset_job("all_assets", selection="*"), cron_schedule="@daily"
        ),
    ],
    sensors=[freshness_check_sensor],
)
