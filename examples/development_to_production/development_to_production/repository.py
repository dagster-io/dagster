import os

from dagster_snowflake import build_snowflake_io_manager
from dagster_snowflake_pandas import SnowflakePandasTypeHandler
from development_to_production.assets import comments, items, stories
from development_to_production.resources import hn_api_client

from dagster import repository, with_resources

# the snowflake io manager can be initialized to handle different data types
# here we use the pandas type handler so we can store pandas DataFrames
snowflake_io_manager = build_snowflake_io_manager([SnowflakePandasTypeHandler()])


@repository
def repo():
    resource_defs = {
        "local": {
            "hn_client": hn_api_client,
            "snowflake_io_manager": snowflake_io_manager.configured(
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
            "snowflake_io_manager": snowflake_io_manager.configured(
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
            "snowflake_io_manager": snowflake_io_manager.configured(
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


def get_repo(name):
    from dagster import op, job

    @op
    def x():
        return 1

    @job
    def xx():
        x()

    @repository(name=name)
    def _repo():
        print("************Name", name)
        return [xx]

    return _repo


a = get_repo("a")
