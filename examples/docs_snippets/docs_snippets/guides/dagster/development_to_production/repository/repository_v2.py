import os

from dagster_snowflake_pandas import snowflake_pandas_io_manager
from development_to_production.assets import comments, items, stories

from dagster import repository, with_resources

# start
# repository.py

# Note that storing passwords in configuration is bad practice. It will be resolved soon.
@repository
def repo():
    resource_defs = {
        "local": {
            "snowflake_io_manager": snowflake_pandas_io_manager.configured(
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
            "snowflake_io_manager": snowflake_pandas_io_manager.configured(
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
