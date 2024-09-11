from dagster_snowflake import SnowflakeResource

import dagster as dg


@dg.asset
def my_table(snowflake: SnowflakeResource):
    with snowflake.get_connection() as conn:
        return conn.cursor().execute_query("SELECT * FROM foo")


defs = dg.Definitions(
    assets=[my_table],
    resources={
        "snowflake": SnowflakeResource(
            account="snowflake account",
            user="snowflake user",
            password=dg.EnvVar("SNOWFLAKE_PASSWORD"),
            database="snowflake database",
            schema="snowflake schema",
            warehouse="snowflake warehouse",
        )
    },
)
