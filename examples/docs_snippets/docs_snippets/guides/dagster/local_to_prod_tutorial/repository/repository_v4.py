import os

from dagster_snowflake import build_snowflake_io_manager
from dagster_snowflake_pandas import SnowflakePandasTypeHandler

from dagster import repository, with_resources

from ..assets import comments, items, stories
from ..resources.resources_v1 import hn_api_client

# the snowflake io manager can be initialized to handle different data types
# here we use the pandas type handler so we can store pandas DataFrames
snowflake_io_manager = build_snowflake_io_manager([SnowflakePandasTypeHandler()])

# start
# repository.py


@repository
def repo():
    resource_defs = {
        "local": {
            "hn_client": hn_api_client,
            "io_manager": snowflake_io_manager.configured(
                {
                    "account": "abc1234.us-east-1",
                    "user": "me@company.com",
                    "password": "my_super_secret_password",
                    "database": "SANDBOX",
                    "schema": "ALICE",
                }
            ),
        },
        "production": {
            "hn_client": hn_api_client,
            "io_manager": snowflake_io_manager.configured(
                {
                    "account": "abc1234.us-east-1",
                    "user": "dev@company.com",
                    "password": "company_super_secret_password",
                    "database": "PRODUCTION",
                    "schema": "HACKER_NEWS",
                }
            ),
        },
    }
    deployment_name = os.environ.get("DAGSTER_DEPLOYMENT", "local")

    return [
        with_resources(
            [items, comments, stories], resource_defs=resource_defs[deployment_name]
        )
    ]


# end
