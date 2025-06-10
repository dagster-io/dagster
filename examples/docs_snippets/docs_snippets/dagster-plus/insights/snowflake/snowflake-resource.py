from dagster_snowflake import SnowflakeResource

import dagster as dg


@dg.definitions
def resources() -> dg.Definitions:
    return dg.Definitions(
        resources={
            "snowflake": SnowflakeResource(
                user=dg.EnvVar("SNOWFLAKE_USER"), password=dg.EnvVar("SNOWFLAKE_PASSWORD")
            ),
        }
    )
