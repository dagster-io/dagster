# ruff: isort: skip_file
import json
import os

import dagster as dg
from dagster_dbt.cloud_v2.asset_decorator import dbt_cloud_assets
from dagster_dbt.cloud_v2.resources import DbtCloudCredentials, DbtCloudWorkspace
from dagster_dbt.cloud_v2.sensor_builder import build_dbt_cloud_polling_sensor

# Define credentials
creds = DbtCloudCredentials(
    account_id=os.getenv("DBT_CLOUD_ACCOUNT_ID"),
    access_url=os.getenv("DBT_CLOUD_ACCESS_URL"),
    token=os.getenv("DBT_CLOUD_TOKEN"),
)

# Define the workspace
workspace = DbtCloudWorkspace(
    credentials=creds,
    project_id=os.getenv("DBT_CLOUD_PROJECT_ID"),
    environment_id=os.getenv("DBT_CLOUD_ENVIRONMENT_ID"),
)


# start_daily_partitioned
@dbt_cloud_assets(
    workspace=workspace,
    partitions_def=dg.DailyPartitionsDefinition(start_date="2024-01-01"),
)
def my_partitioned_dbt_cloud_assets(
    context: dg.AssetExecutionContext, dbt_cloud: DbtCloudWorkspace
):
    time_window = context.partition_time_window
    dbt_vars = {
        "min_date": time_window.start.isoformat(),
        "max_date": time_window.end.isoformat(),
    }

    yield from dbt_cloud.cli(
        args=["build", "--vars", json.dumps(dbt_vars)],
        context=context,
    ).wait()


# end_daily_partitioned


# start_static_partitioned
@dbt_cloud_assets(
    workspace=workspace,
    partitions_def=dg.StaticPartitionsDefinition(["us", "eu", "apac"]),
)
def my_region_dbt_cloud_assets(
    context: dg.AssetExecutionContext, dbt_cloud: DbtCloudWorkspace
):
    region = context.partition_key
    dbt_vars = {"target_region": region}

    yield from dbt_cloud.cli(
        args=["build", "--vars", json.dumps(dbt_vars)],
        context=context,
    ).wait()


# end_static_partitioned
