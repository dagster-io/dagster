import os


def get_env_var(var_name: str) -> str:
    value = os.getenv(var_name)
    if not value:
        raise Exception(f"{var_name} is not set")
    return value


def get_dbt_cloud_account_id() -> str:
    return get_env_var("TEST_DBT_CLOUD_ACCOUNT_ID")


def get_dbt_cloud_personal_token() -> str:
    return get_env_var("TEST_DBT_CLOUD_PERSONAL_TOKEN")


def get_dbt_cloud_region() -> str:
    return get_env_var("TEST_DBT_CLOUD_REGION")


def get_dbt_cloud_account_prefix() -> str:
    return get_env_var("TEST_DBT_CLOUD_ACCOUNT_PREFIX")


def get_dbt_cloud_environment_id() -> str:
    return get_env_var("TEST_DBT_CLOUD_ENVIRONMENT_ID")
