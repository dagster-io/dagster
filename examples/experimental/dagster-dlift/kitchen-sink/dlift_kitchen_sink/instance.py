from dagster_dlift.client import UnscopedDbtCloudClient
from dagster_dlift.project import DbtCloudCredentials, DBTCloudProjectEnvironment
from dagster_dlift.test.utils import get_env_var

from dlift_kitchen_sink.constants import TEST_ENV_NAME


def get_project() -> DBTCloudProjectEnvironment:
    return DBTCloudProjectEnvironment(
        credentials=DbtCloudCredentials(
            account_id=int(get_env_var("KS_DBT_CLOUD_ACCOUNT_ID")),
            token=get_env_var("KS_DBT_CLOUD_TOKEN"),
            access_url=get_env_var("KS_DBT_CLOUD_ACCESS_URL"),
            discovery_api_url=get_env_var("KS_DBT_CLOUD_DISCOVERY_API_URL"),
        ),
        project_id=get_project_id(),
        environment_id=get_environment_id(),
    )


def get_unscoped_client() -> UnscopedDbtCloudClient:
    return UnscopedDbtCloudClient(
        account_id=int(get_env_var("KS_DBT_CLOUD_ACCOUNT_ID")),
        token=get_env_var("KS_DBT_CLOUD_TOKEN"),
        access_url=get_env_var("KS_DBT_CLOUD_ACCESS_URL"),
        discovery_api_url=get_env_var("KS_DBT_CLOUD_DISCOVERY_API_URL"),
    )


def get_environment_id() -> int:
    return get_unscoped_client().get_environment_id_by_name(TEST_ENV_NAME)


def get_project_id() -> int:
    return int(get_env_var("KS_DBT_CLOUD_PROJECT_ID"))
