import os

from dagster_snowflake_pandas import SnowflakePandasIOManager

from dagster import Definitions, EnvVar
from development_to_production.assets.hacker_news_assets import comments, items, stories

# start
# definitions.py


resources = {
    "local": {
        "snowflake_io_manager": SnowflakePandasIOManager(
            account="abc1234.us-east-1",
            user=EnvVar("DEV_SNOWFLAKE_USER"),
            password=EnvVar("DEV_SNOWFLAKE_PASSWORD"),
            database="LOCAL",
            schema=EnvVar("DEV_SNOWFLAKE_SCHEMA"),
        ),
    },
    "production": {
        "snowflake_io_manager": SnowflakePandasIOManager(
            account="abc1234.us-east-1",
            user="system@company.com",
            password=EnvVar("SYSTEM_SNOWFLAKE_PASSWORD"),
            database="PRODUCTION",
            schema="HACKER_NEWS",
        ),
    },
}
deployment_name = os.getenv("DAGSTER_DEPLOYMENT", "local")

defs = Definitions(
    assets=[items, comments, stories], resources=resources[deployment_name]
)

# end


# start_staging

resources = {
    "local": {...},
    "production": {...},
    "staging": {
        "snowflake_io_manager": SnowflakePandasIOManager(
            account="abc1234.us-east-1",
            user="system@company.com",
            password=EnvVar("SYSTEM_SNOWFLAKE_PASSWORD"),
            database="STAGING",
            schema="HACKER_NEWS",
        ),
    },
}

# end_staging

from ..resources.resources_v1 import HNAPIClient

# start_hn_resource

resource_defs = {
    "local": {"hn_client": HNAPIClient(), "snowflake_io_manager": {...}},
    "production": {"hn_client": HNAPIClient(), "snowflake_io_manager": {...}},
    "staging": {"hn_client": HNAPIClient(), "snowflake_io_manager": {...}},
}

# end_hn_resource
