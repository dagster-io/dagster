import os

import dagster as dg
from dagster_dbt.cloud.resources import (
    DbtCloudCredentials,
    DbtCloudWorkspace,
    load_dbt_cloud_asset_specs,
)

creds = DbtCloudCredentials(
    account_id=os.getenv("DBT_CLOUD_ACCOUNT_ID"),
    access_url=os.getenv("DBT_CLOUD_ACCESS_URL"),
    token=os.getenv("DBT_CLOUD_TOKEN"),
)

workspace = DbtCloudWorkspace(
    credentials=creds,
    project_id=os.getenv("DBT_CLOUD_PROJECT_ID"),
    environment_id=os.getenv("DBT_CLOUD_ENVIRONMENT_ID"),
)

specs = load_dbt_cloud_asset_specs(workspace=workspace)

defs = dg.Definitions(assets=specs)