import os

from dagster_dbt.cloud_v2.resources import DbtCloudCredentials, DbtCloudWorkspace

dbt_cloud_workspace = DbtCloudWorkspace(
    credentials=DbtCloudCredentials(
        account_id=os.getenv("KS_DBT_CLOUD_ACCOUNT_ID"),
        access_url=os.getenv("KS_DBT_CLOUD_ACCESS_URL"),
        token=os.getenv("KS_DBT_CLOUD_TOKEN"),
    ),
    project_id=os.getenv("KS_DBT_CLOUD_PROJECT_ID"),
    environment_id=os.getenv("KS_DBT_CLOUD_ENVIRONMENT_ID"),
)
