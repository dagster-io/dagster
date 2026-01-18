from dagster_dbt.cloud_v2.resources import DbtCloudCredentials, DbtCloudWorkspace

from dagster_dbt_cloud_kitchen_sink.utils import get_env_var


def get_project_id() -> int:
    return int(get_env_var("KS_DBT_CLOUD_PROJECT_ID"))


def get_environment_id() -> int:
    return int(get_env_var("KS_DBT_CLOUD_ENVIRONMENT_ID"))


def get_dbt_cloud_workspace() -> DbtCloudWorkspace:
    return DbtCloudWorkspace(
        credentials=DbtCloudCredentials(
            account_id=int(get_env_var("KS_DBT_CLOUD_ACCOUNT_ID")),
            access_url=get_env_var("KS_DBT_CLOUD_ACCESS_URL"),
            token=get_env_var("KS_DBT_CLOUD_TOKEN"),
        ),
        project_id=get_project_id(),
        environment_id=get_environment_id(),
    )
