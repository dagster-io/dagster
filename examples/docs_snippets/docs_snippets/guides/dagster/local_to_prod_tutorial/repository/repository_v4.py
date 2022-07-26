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

# Note: there are multiple issues with how this config is specified, mainly that
# passwords are being stored in code. This will be addressed next.
@repository
def repo():
    resource_defs = {
        "local": {
            "io_manager": snowflake_io_manager.configured(
                {
                    "account": "abc1234.us-east-1",
                    "user": "me@company.com",
                    "password": "my_super_secret_password",  # password in config is bad practice
                    "database": "SANDBOX",
                    "schema": "ALICE",
                }
            ),
        },
        "production": {
            "io_manager": snowflake_io_manager.configured(
                {
                    "account": "abc1234.us-east-1",
                    "user": "dev@company.com",
                    "password": "company_super_secret_password",  # password in config is bad practice
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
