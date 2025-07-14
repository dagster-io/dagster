# ruff: isort: skip_file
import os

import dagster as dg
from dagster_dbt.cloud_v2.resources import (
    DbtCloudCredentials,
    DbtCloudWorkspace,
    load_dbt_cloud_asset_specs,
)
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

# Use the integration to create asset specs for models in the workspace
dbt_cloud_asset_specs = load_dbt_cloud_asset_specs(workspace=workspace)

# Build a sensor which will poll dbt Cloud for updates on runs/materialization history
# and dbt Cloud Assets
dbt_cloud_polling_sensor = build_dbt_cloud_polling_sensor(workspace=workspace)
