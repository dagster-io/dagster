# pyright: reportGeneralTypeIssues=none
# pyright: reportOptionalMemberAccess=none

# start
from dagster_snowflake import SnowflakeResource

from dagster import Definitions, EnvVar, asset

# this example executes a query against the IRIS_DATASET table created in Step 2 of the
# Using Dagster with Snowflake tutorial


@asset
def small_petals(snowflake: SnowflakeResource):
    query = """
        create or replace table iris.small_petals as (
            SELECT * 
            FROM iris.iris_dataset
            WHERE species = 'petal_length_cm' < 1 AND 'petal_width_cm' < 1
        );
    """

    with snowflake.get_connection() as conn:
        conn.cursor.execute(query)


defs = Definitions(
    assets=[small_petals],
    resources={
        "snowflake": SnowflakeResource(
            account="abc1234.us-east-1",
            user=EnvVar("SNOWFLAKE_USER"),
            password=EnvVar("SNOWFLAKE_PASSWORD"),
            database="FLOWERS",
            schema="IRIS",
        )
    },
)

# end
