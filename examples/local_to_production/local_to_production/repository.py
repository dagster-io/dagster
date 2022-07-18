from dagster_snowflake import build_snowflake_io_manager
from dagster_snowflake_pandas import SnowflakePandasTypeHandler
from local_to_production.assets import comments, items, stories
from local_to_production.resources import hn_api_client

from dagster import repository, with_resources

snowflake_io_manager = build_snowflake_io_manager([SnowflakePandasTypeHandler()])


@repository
def repo():
    resource_defs = {
        "hn_client": hn_api_client,
        "io_manager": snowflake_io_manager.configured(
            {
                "account": {"env": "SNOWFLAKE_ACCOUNT"},
                "user": {"env": "SNOWFLAKE_USER"},
                "password": {
                    "env": "SNOWFLAKE_PASSWORD",
                },
                "database": {"env": "SNOWFLAKE_DATABASE"},
            }
        ),
    }

    return [*with_resources([items, comments, stories], resource_defs=resource_defs)]
