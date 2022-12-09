import os

from dagster_snowflake_pandas import snowflake_pandas_io_manager
from development_to_production.assets import comments, items, stories
from development_to_production.resources import hn_api_client

from dagster import repository, with_resources


@repository
def repo():
    resource_defs = {
        "local": {
            "hn_client": hn_api_client,
            "snowflake_io_manager": snowflake_pandas_io_manager.configured(
                {
                    "account": "abc1234.us-east-1",
                    "user": {"env": "DEV_SNOWFLAKE_USER"},
                    "password": {"env": "DEV_SNOWFLAKE_PASSWORD"},
                    "database": "LOCAL",
                    "schema": {"env": "DEV_SNOWFLAKE_SCHEMA"},
                }
            ),
        },
        "staging": {
            "hn_client": hn_api_client,
            "snowflake_io_manager": snowflake_pandas_io_manager.configured(
                {
                    "account": "abc1234.us-east-1",
                    "user": "system@company.com",
                    "password": {"env": "SYSTEM_SNOWFLAKE_PASSWORD"},
                    "database": "STAGING",
                    "schema": "HACKER_NEWS",
                }
            ),
        },
        "production": {
            "hn_client": hn_api_client,
            "snowflake_io_manager": snowflake_pandas_io_manager.configured(
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
        *with_resources([items, comments, stories], resource_defs=resource_defs[deployment_name])
    ]
