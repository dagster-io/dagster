from dagster import (
    Definitions,
    ScheduleDefinition,
    define_asset_job,
    load_assets_from_package_module,
)
from dagster_airbyte import AirbyteResource
from dagster_dbt import DbtCli

from . import assets
from .db_io_manager import DbIOManager
from .utils.constants import AIRBYTE_CONFIG, DBT_CONFIG, POSTGRES_CONFIG

defs = Definitions(
    assets=load_assets_from_package_module(assets),
    resources={
        "airbyte": AirbyteResource(**AIRBYTE_CONFIG),
        "dbt": DbtCli(**DBT_CONFIG),
        "db_io_manager": DbIOManager(**POSTGRES_CONFIG),
    },
    schedules=[
        # update all assets once a day
        ScheduleDefinition(
            job=define_asset_job("all_assets", selection="*"), cron_schedule="@daily"
        ),
    ],
)
