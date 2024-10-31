from dagster_dlift.cloud_instance import DbtCloudInstance
from dagster_dlift.test.utils import get_env_var


def get_instance() -> DbtCloudInstance:
    return DbtCloudInstance(
        account_id=get_env_var("KS_DBT_CLOUD_ACCOUNT_ID"),
        token=get_env_var("KS_DBT_CLOUD_TOKEN"),
        access_url=get_env_var("KS_DBT_CLOUD_ACCESS_URL"),
        discovery_api_url=get_env_var("KS_DBT_CLOUD_DISCOVERY_API_URL"),
    )
