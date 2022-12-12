from dagster_airbyte import airbyte_resource
from dagster_dbt import dbt_cli_resource

from dagster import (
    Definitions,
    ScheduleDefinition,
    define_asset_job,
    load_assets_from_package_module,
)

from . import assets
from .db_io_manager import db_io_manager
from .utils.constants import AIRBYTE_CONFIG, DBT_CONFIG, POSTGRES_CONFIG

defs = Definitions(
    assets=load_assets_from_package_module(assets),
    resources={
        "airbyte": airbyte_resource.configured(AIRBYTE_CONFIG),
        "dbt": dbt_cli_resource.configured(DBT_CONFIG),
        "db_io_manager": db_io_manager.configured(POSTGRES_CONFIG),
    },
    schedules=[
        # update all assets once a day
        ScheduleDefinition(
            job=define_asset_job("all_assets", selection="*"), cron_schedule="@daily"
        ),
    ],
)
