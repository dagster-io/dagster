from dagster import repository, with_resources
from ..assets import comments, items, stories
from dagster_snowflake import build_snowflake_io_manager
from dagster_snowflake_pandas import SnowflakePandasTypeHandler
import os

# the snowflake io manager can be initialized to handle different data types
# here we use the pandas type handler so we can store pandas DataFrames
snowflake_io_manager = build_snowflake_io_manager([SnowflakePandasTypeHandler()])

# start_repository
@repository
def repo():
    snowflake_config = {
        "account": {"env": "SNOWFLAKE_ACCOUNT"},
        "user": {"env": "SNOWFLAKE_USER"},
        "password": {"env": "SNOWFLAKE_PASSWORD"},
        "schema": "HACKER_NEWS",
    }
    resource_defs = {
        "branch": {
            "snowflake_io_manager": snowflake_io_manager.configured(
                {
                    **snowflake_config,
                    "database": f"PRODUCTION_CLONE_{os.getenv('DAGSTER_CLOUD_PULL_REQUEST_ID')}",
                }
            ),
        },
        "production": {
            "snowflake_io_manager": snowflake_io_manager.configured(
                {
                    **snowflake_config,
                    "database": "PRODUCTION",
                }
            ),
        },
    }

    def get_current_env():
        is_branch_depl = os.getenv("DAGSTER_CLOUD_IS_BRANCH_DEPLOYMENT")
        assert is_branch_depl != None  # env var must be set
        return "branch" if is_branch_depl else "prod"

    return [
        with_resources([items, comments, stories], resource_defs=resource_defs[get_current_env()]),
    ]


# end_repository
