import os

from dagster_snowflake import build_snowflake_io_manager
from dagster_snowflake_pandas import SnowflakePandasTypeHandler

from dagster import repository, with_resources

from ..assets import comments, items, stories

# the snowflake io manager can be initialized to handle different data types
# here we use the pandas type handler so we can store pandas DataFrames
snowflake_io_manager = build_snowflake_io_manager([SnowflakePandasTypeHandler()])

# start
# repository.py


@repository
def repo():
    resource_defs = {
        "local": {
            "io_manager": snowflake_io_manager.configured(
                {
                    "account": "abc1234.us-east-1",
                    "user": {"env": "DEV_SNOWFLAKE_USER"},
                    "password": {"env": "DEV_SNOWFLAKE_PASSWORD"},
                    "database": "LOCAL",
                    "schema": {"env": "DEV_SNOWFLAKE_SCHEMA"},
                }
            ),
        },
        "production": {
            "io_manager": snowflake_io_manager.configured(
                {
                    "account": "abc1234.us-east-1",
                    "user": "system@company.com",
                    "password": {"env": "SYSTEM_SNOWFLAKE_PASSWORD"},
                    "database": "PRODUCTION",
                    "schema": "HACKER_NEWS",
                }
            ),
        },
    }
    deployment_name = os.getenv("DAGSTER_DEPLOYMENT", "local")

    return [
        with_resources(
            [items, comments, stories], resource_defs=resource_defs[deployment_name]
        )
    ]


# end


# start_staging

resource_defs = {
    "local": {...},
    "production": {...},
    "staging": {
        "io_manager": snowflake_io_manager.configured(
            {
                "account": "abc1234.us-east-1",
                "user": "system@company.com",
                "password": {"env": "SYSTEM_SNOWFLAKE_PASSWORD"},
                "database": "STAGING",
                "schema": "HACKER_NEWS",
            }
        ),
    },
}

# end_staging
