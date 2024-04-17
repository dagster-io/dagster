import os

from dagster import Definitions, EnvVar
from dagster_snowflake import SnowflakeResource

from development_to_production.assets import comments, items, stories
from development_to_production.resources import HNAPIClient

resource_defs = {
    "local": {
        "hn_client": HNAPIClient(),
         "snowflake_resource": SnowflakeResource(
            account="abc1234.us-east-1",
            user=EnvVar("DEV_SNOWFLAKE_USER"),
            password=EnvVar("DEV_SNOWFLAKE_PASSWORD"),
            database="TESTDB",
            schema=EnvVar("DEV_SNOWFLAKE_SCHEMA"),
        ),
    },
    "staging": {
        "hn_client": HNAPIClient(),
         "snowflake_resource": SnowflakeResource(
            account="abc1234.us-east-1",
            user="system@company.com",
            password=EnvVar("SYSTEM_SNOWFLAKE_PASSWORD"),
            database="STAGING",
            schema="HACKER_NEWS",
        ),
    },
    "production": {
        "hn_client": HNAPIClient(),
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
    assets=[items, comments, stories],
    resources=resource_defs[deployment_name],
)
