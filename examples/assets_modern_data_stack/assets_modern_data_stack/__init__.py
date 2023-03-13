from dagster import (
    Definitions,
    ScheduleDefinition,
    define_asset_job,
    load_assets_from_package_module,
)
from dagster_airbyte import airbyte_resource
from dagster_dbt import dbt_cli_resource

from assets_modern_data_stack import assets
from assets_modern_data_stack.db_io_manager import db_io_manager, POSTGRES_CONFIG
from assets_modern_data_stack.assets.airbyte_iaac import airbyte_instance
from assets_modern_data_stack.assets.modern_data_stack import DBT_CONFIG

defs = Definitions(
    assets=load_assets_from_package_module(assets),
    resources={
        # "airbyte": airbyte_instance,
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
