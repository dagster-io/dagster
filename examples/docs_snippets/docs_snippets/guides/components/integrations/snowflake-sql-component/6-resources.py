import dagster as dg
from dagster_snowflake import SnowflakeResource

defs = dg.Definitions(
    resources={
        "snowflake": SnowflakeResource(
            account=dg.EnvVar("SNOWFLAKE_ACCOUNT"),
            user=dg.EnvVar("SNOWFLAKE_USER"),
            password=dg.EnvVar("SNOWFLAKE_PASSWORD"),
            database=dg.EnvVar("SNOWFLAKE_DATABASE"),
            schema=dg.EnvVar("SNOWFLAKE_SCHEMA"),
        )
    }
)
