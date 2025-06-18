import os

import dagster as dg

from dagster_snowflake_pandas import SnowflakePandasIOManager


@dg.definitions
def resources() -> dg.Definitions:
    return dg.Definitions(
        resources={
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
    )


deployment_name = os.getenv("DAGSTER_DEPLOYMENT", "local")

defs = dg.Definitions(resources=resources[deployment_name])
