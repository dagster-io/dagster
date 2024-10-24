from dagster_dlift.client import DbtCloudClient
from dagster_dlift.test.utils import get_env_var

from dlift_kitchen_sink.constants import TEST_ENV_NAME


def get_instance() -> DbtCloudClient:
    return DbtCloudClient(
        account_id=int(get_env_var("KS_DBT_CLOUD_ACCOUNT_ID")),
        token=get_env_var("KS_DBT_CLOUD_TOKEN"),
        access_url=get_env_var("KS_DBT_CLOUD_ACCESS_URL"),
        discovery_api_url=get_env_var("KS_DBT_CLOUD_DISCOVERY_API_URL"),
    )


def get_environment_id() -> int:
    return get_instance().get_environment_id_by_name(TEST_ENV_NAME)


def get_project_id() -> int:
    return int(get_env_var("KS_DBT_CLOUD_PROJECT_ID"))
