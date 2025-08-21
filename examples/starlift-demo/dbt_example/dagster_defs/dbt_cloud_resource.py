from dagster_dbt.cloud_v2.resources import DbtCloudCredentials, DbtCloudWorkspace

from .dbt_cloud_utils import get_env_var


def get_dbt_cloud_workspace() -> DbtCloudWorkspace:
    dbt_cloud_creds = DbtCloudCredentials(
        account_id=int(get_env_var("KS_DBT_CLOUD_ACCOUNT_ID")),
        access_url=get_env_var("KS_DBT_CLOUD_ACCESS_URL"),
        token=get_env_var("KS_DBT_CLOUD_TOKEN"),
    )

    dbt_cloud_workspace = DbtCloudWorkspace(
        credentials=dbt_cloud_creds,
        project_id=int(get_env_var("KS_DBT_CLOUD_PROJECT_ID")),
        environment_id=int(get_env_var("KS_DBT_CLOUD_ENVIRONMENT_ID")),
    )

    return dbt_cloud_workspace
