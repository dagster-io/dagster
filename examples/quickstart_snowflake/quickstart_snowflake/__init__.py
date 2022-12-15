from dagster_snowflake_pandas import snowflake_pandas_io_manager

from dagster import (
    Definitions,
    ScheduleDefinition,
    define_asset_job,
    load_assets_from_package_module,
)

from . import assets

daily_refresh_schedule = ScheduleDefinition(
    job=define_asset_job(name="all_assets_job"), cron_schedule="0 0 * * *"
)


defs = Definitions(
    assets=load_assets_from_package_module(assets),
    resources={
        "io_manager": snowflake_pandas_io_manager.configured(
            # Read about using environment variables and secrets in Dagster:
            # https://docs.dagster.io/guides/dagster/using-environment-variables-and-secrets
            {
                "account": {"env": "SNOWFLAKE_ACCOUNT"},
                "user": {"env": "SNOWFLAKE_USER"},
                "password": {"env": "SNOWFLAKE_PASSWORD"},
                "warehouse": {"env": "SNOWFLAKE_WAREHOUSE"},
                "database": {"env": "SNOWFLAKE_DATABASE"},
                "schema": {"env": "SNOWFLAKE_SCHEMA"},
            }
        ),
    },
    schedules=[daily_refresh_schedule],
)
