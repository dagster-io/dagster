import os

from dagster_snowflake import SnowflakeResource

from dagster import Definitions, EnvVar
from development_to_production.assets import comments, items, stories

# start
# __init__.py


resources = {
    "local": {
        "snowflake_resource": SnowflakeResource(
            account="abc1234.us-east-1",
            user=EnvVar("DEV_SNOWFLAKE_USER"),
            password=EnvVar("DEV_SNOWFLAKE_PASSWORD"),
            database="TESTDB",
            schema=EnvVar("DEV_SNOWFLAKE_SCHEMA"),
        ),
    },
    "production": {
        "snowflake_resource": SnowflakeResource(
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
        "snowflake_resource": SnowflakeResource(
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
    "local": {"hn_client": HNAPIClient(), "snowflake_resource": {...}},
    "production": {"hn_client": HNAPIClient(), "snowflake_resource": {...}},
    "staging": {"hn_client": HNAPIClient(), "snowflake_resource": {...}},
}

# end_hn_resource
