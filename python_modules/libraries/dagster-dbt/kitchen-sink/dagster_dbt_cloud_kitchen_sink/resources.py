import os

from dagster_dbt.cloud_v2.resources import DbtCloudCredentials, DbtCloudWorkspace


def get_project_id() -> int:
    return int(os.getenv("KS_DBT_CLOUD_PROJECT_ID"))


def get_environment_id() -> int:
    return int(os.getenv("KS_DBT_CLOUD_ENVIRONMENT_ID"))


def get_dbt_cloud_workspace() -> DbtCloudWorkspace:
    return DbtCloudWorkspace(
        credentials=DbtCloudCredentials(
            account_id=os.getenv("KS_DBT_CLOUD_ACCOUNT_ID"),
            access_url=os.getenv("KS_DBT_CLOUD_ACCESS_URL"),
            token=os.getenv("KS_DBT_CLOUD_TOKEN"),
        ),
        project_id=get_project_id(),
        environment_id=get_environment_id(),
    )
