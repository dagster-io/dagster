from dagster import (
    ScheduleDefinition,
    define_asset_job,
    load_assets_from_package_module,
    repository,
    with_resources,
)
from dagster_snowflake import build_snowflake_io_manager
from dagster_snowflake_pandas import SnowflakePandasTypeHandler

from . import assets

daily_refresh_schedule = ScheduleDefinition(
    job=define_asset_job(name="all_assets_job"), cron_schedule="0 0 * * *"
)


@repository
def quickstart_snowflake():
    return [
        *with_resources(
            load_assets_from_package_module(assets),
            resource_defs={
                "io_manager": build_snowflake_io_manager([SnowflakePandasTypeHandler()]).configured(
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
        ),
        daily_refresh_schedule,
    ]
