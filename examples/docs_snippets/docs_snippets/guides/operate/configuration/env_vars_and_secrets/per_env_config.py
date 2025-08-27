import os

from dagster_snowflake_pandas import SnowflakePandasIOManager

import dagster as dg


def resources_by_deployment() -> dict:
    return {
        "local": {
            "snowflake_io_manager": SnowflakePandasIOManager(
                account="abc1234.us-east-1",
                user=dg.EnvVar("DEV_SNOWFLAKE_USER"),
                password=dg.EnvVar("DEV_SNOWFLAKE_PASSWORD"),
                database="LOCAL",
                schema=dg.EnvVar("DEV_SNOWFLAKE_SCHEMA"),
            ),
        },
        "production": {
            "snowflake_io_manager": SnowflakePandasIOManager(
                account="abc1234.us-east-1",
                user="system@company.com",
                password=dg.EnvVar("SYSTEM_SNOWFLAKE_PASSWORD"),
                database="PRODUCTION",
                schema="HACKER_NEWS",
            ),
        },
    }


@dg.definitions
def resources() -> dg.Definitions:
    deployment_name = os.getenv("DAGSTER_DEPLOYMENT", "local")
    return dg.Definitions(resources=resources_by_deployment()[deployment_name])
