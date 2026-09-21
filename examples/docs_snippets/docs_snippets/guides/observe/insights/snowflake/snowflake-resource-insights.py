from dagster_cloud.dagster_insights import (
    InsightsSnowflakeResource,
    create_snowflake_insights_asset_and_schedule,
)

import dagster as dg

# highlight-start
insights_definitions = create_snowflake_insights_asset_and_schedule(
    start_date="2024-01-01-00:00"
)
# highlight-end


@dg.asset
# highlight-start
def snowflake_asset(snowflake: InsightsSnowflakeResource):
    # highlight-end
    with snowflake.get_connection() as conn:
        conn.cursor().execute("select 1")


defs = dg.Definitions(
    # highlight-start
    assets=[snowflake_asset, *insights_definitions.assets],
    schedules=[insights_definitions.schedule],
    # highlight-end
    resources={
        # highlight-start
        "snowflake": InsightsSnowflakeResource(
            user=dg.EnvVar("SNOWFLAKE_USER"), password=dg.EnvVar("SNOWFLAKE_PASSWORD")
        ),
        # highlight-end
    },
)
