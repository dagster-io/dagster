import os

from dagster_snowflake_pandas import SnowflakePandasIOManager

import dagster as dg


@dg.definitions
def resources() -> dg.Definitions:
    return dg.Definitions(
        resources={
            "local": {
                "snowflake_io_manager": SnowflakePandasIOManager(
                    account="abc1234.us-east-1",
                    # highlight-start
                    user=dg.EnvVar("DEV_SNOWFLAKE_USER"),
                    password=dg.EnvVar("DEV_SNOWFLAKE_PASSWORD"),
                    # highlight-end
                    database="LOCAL",
                    # highlight-start
                    schema=dg.EnvVar("DEV_SNOWFLAKE_SCHEMA"),
                    # highlight-end
                ),
            },
            "production": {
                "snowflake_io_manager": SnowflakePandasIOManager(
                    account="abc1234.us-east-1",
                    user="system@company.com",
                    # highlight-start
                    password=dg.EnvVar("SYSTEM_SNOWFLAKE_PASSWORD"),
                    # highlight-end
                    database="PRODUCTION",
                    schema="HACKER_NEWS",
                ),
            },
        }
    )


deployment_name = os.getenv("DAGSTER_DEPLOYMENT", "local")

defs = dg.Definitions(resources=resources[deployment_name])
