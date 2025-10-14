import os

from dagster_snowflake_pandas import SnowflakePandasIOManager

import dagster as dg

snowflake_config = {
    "account": "abc1234.us-east-1",
    "user": "system@company.com",
    "password": {"env": "SYSTEM_SNOWFLAKE_PASSWORD"},
    "schema": "HACKER_NEWS",
}

resources = {
    "branch": {
        "snowflake_io_manager": SnowflakePandasIOManager(
            **snowflake_config,
            database=f"PRODUCTION_CLONE_{os.getenv('DAGSTER_CLOUD_PULL_REQUEST_ID')}",
        ),
    },
    "prod": {
        "snowflake_io_manager": SnowflakePandasIOManager(
            **snowflake_config,
            database="PRODUCTION",
        ),
    },
}


def get_current_env():
    is_branch_depl = os.getenv("DAGSTER_CLOUD_IS_BRANCH_DEPLOYMENT") == "1"
    assert is_branch_depl is not None  # env var must be set
    return "branch" if is_branch_depl else "prod"


@dg.definitions
def resources():
    return dg.Definitions(resources=resources[get_current_env()])
