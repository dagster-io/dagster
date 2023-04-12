from dagster import (
    Definitions,
    ScheduleDefinition,
    define_asset_job,
    load_assets_from_package_module,
)
from dagster_gcp_pandas import bigquery_pandas_io_manager

from . import assets

daily_refresh_schedule = ScheduleDefinition(
    job=define_asset_job(name="all_assets_job"), cron_schedule="0 0 * * *"
)


defs = Definitions(
    assets=load_assets_from_package_module(assets),
    resources={
        # Read about using environment variables and secrets in Dagster:
        #   https://docs.dagster.io/guides/dagster/using-environment-variables-and-secrets
        "io_manager": bigquery_pandas_io_manager.configured(
            {"project": {"env": "BIGQUERY_PROJECT_ID"}, "dataset": "hackernews"}
        ),
    },
    schedules=[daily_refresh_schedule],
)
