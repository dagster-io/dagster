import os

from dagster_snowflake import SnowflakeResource
from dagster_snowflake_pandas import SnowflakePandasIOManager

import dagster as dg

from .clone_and_drop_db import clone_prod, drop_prod_clone

snowflake_config = {
    "account": {"env": "SNOWFLAKE_ACCOUNT"},
    "user": {"env": "SNOWFLAKE_USER"},
    "password": {"env": "SNOWFLAKE_PASSWORD"},
    "schema": "HACKER_NEWS",
}

# start_resources
resources = {
    "branch": {
        "snowflake_io_manager": SnowflakePandasIOManager(
            **snowflake_config,
            database=f"PRODUCTION_CLONE_{os.getenv('DAGSTER_CLOUD_PULL_REQUEST_ID')}",
        ),
        "snowflake": SnowflakeResource(
            **snowflake_config,
            database=f"PRODUCTION_CLONE_{os.getenv('DAGSTER_CLOUD_PULL_REQUEST_ID')}",
        ),
    },
    "prod": {
        "snowflake_io_manager": SnowflakePandasIOManager(
            **snowflake_config,
            database="PRODUCTION",
        ),
        "snowflake": SnowflakeResource(**snowflake_config, database="PRODUCTION"),
    },
}


def get_current_env():
    is_branch_depl = os.getenv("DAGSTER_CLOUD_IS_BRANCH_DEPLOYMENT")
    assert is_branch_depl is not None  # env var must be set
    return "branch" if is_branch_depl else "prod"


@dg.definitions
def resources():
    return dg.Definitions(
        resources=resources[get_current_env()],
    )


# end_resources


# start_repository
branch_deployment_jobs = [
    clone_prod.to_job(),
    drop_prod_clone.to_job(),
]


@dg.definitions
def jobs():
    return dg.Definitions(
        jobs=(
            branch_deployment_jobs
            if os.getenv("DAGSTER_CLOUD_IS_BRANCH_DEPLOYMENT") == "1"
            else []
        ),
    )


# end_repository
