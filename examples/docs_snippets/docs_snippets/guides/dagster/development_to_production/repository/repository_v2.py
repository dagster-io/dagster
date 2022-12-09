import os

from dagster_snowflake_pandas import snowflake_pandas_io_manager
from development_to_production.assets import comments, items, stories

from dagster import Definitions

# start
# __init__.py

# Note that storing passwords in configuration is bad practice. It will be resolved soon.
resources = {
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

defs = Definitions(
    assets=[items, comments, stories], resources=resources[deployment_name]
)


# end
