from dagster_snowflake import SnowflakeResource

import dagster as dg


@dg.asset
def snowflake_asset(snowflake: SnowflakeResource):
    with snowflake.get_connection() as conn:
        conn.cursor().execute("select 1")


defs = dg.Definitions(
    assets=[snowflake_asset],
    resources={
        "snowflake": SnowflakeResource(
            user=dg.EnvVar("SNOWFLAKE_USER"), password=dg.EnvVar("SNOWFLAKE_PASSWORD")
        ),
    },
)
