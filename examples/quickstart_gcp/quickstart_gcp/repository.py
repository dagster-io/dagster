from dagster import (
    ScheduleDefinition,
    define_asset_job,
    load_assets_from_package_module,
    repository,
    with_resources,
)

from . import assets
from .io_managers import bigquery_pandas_io_manager

daily_refresh_schedule = ScheduleDefinition(
    job=define_asset_job(name="all_assets_job"), cron_schedule="0 0 * * *"
)


@repository
def quickstart_gcp():
    return [
        *with_resources(
            load_assets_from_package_module(assets),
            resource_defs={
                # Read about using environment variables and secrets in Dagster:
                #   https://docs.dagster.io/guides/dagster/using-environment-variables-and-secrets
                "io_manager": bigquery_pandas_io_manager.configured(
                    {
                        "credentials": {"env": "BIGQUERY_SERVICE_ACCOUNT_CREDENTIALS"},
                        "project_id": {"env": "BIGQUERY_PROJECT_ID"},
                    }
                ),
            },
        ),
        daily_refresh_schedule,
    ]
