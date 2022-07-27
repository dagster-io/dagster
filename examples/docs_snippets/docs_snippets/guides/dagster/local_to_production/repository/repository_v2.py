import os

from dagster_snowflake import build_snowflake_io_manager
from dagster_snowflake_pandas import SnowflakePandasTypeHandler
from local_to_production.assets import comments, items, stories

from dagster import repository, with_resources

# the snowflake io manager can be initialized to handle different data types
# here we use the pandas type handler so we can store pandas DataFrames
snowflake_io_manager = build_snowflake_io_manager([SnowflakePandasTypeHandler()])

# start
# repository.py

# Note that storing passwords in configuration is bad practice. It will be resolved soon.
@repository
def repo():
    resource_defs = {
        "local": {
            "snowflake_io_manager": snowflake_io_manager.configured(
                {
                    "account": "abc1234.us-east-1",
                    "user": "me@company.com",
                    # password in config is bad practice
                    "password": "my_super_secret_password",
                    "database": "LOCAL",
                    "schema": "ALICE",
                }
            ),
        },
        "production": {
            "snowflake_io_manager": snowflake_io_manager.configured(
                {
                    "account": "abc1234.us-east-1",
                    "user": "dev@company.com",
                    # password in config is bad practice
                    "password": "company_super_secret_password",
                    "database": "PRODUCTION",
                    "schema": "HACKER_NEWS",
                }
            ),
        },
    }
    deployment_name = os.getenv("DAGSTER_DEPLOYMENT", "local")

    return [
        *with_resources(
            [items, comments, stories], resource_defs=resource_defs[deployment_name]
        )
    ]


# end
