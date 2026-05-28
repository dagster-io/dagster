import dagster as dg
from dagster_snowflake import SnowflakeResource


@dg.definitions
def resources() -> dg.Definitions:
    return dg.Definitions(
        resources={
            "snowflake": SnowflakeResource(
                account=dg.EnvVar("SNOWFLAKE_ACCOUNT"),
                user=dg.EnvVar("SNOWFLAKE_USER"),
                password=dg.EnvVar("SNOWFLAKE_PASSWORD"),
                database=dg.EnvVar("SNOWFLAKE_DATABASE"),
                warehouse=dg.EnvVar("SNOWFLAKE_WAREHOUSE"),
                schema=dg.EnvVar("SNOWFLAKE_SCHEMA"),
            )
        }
    )
