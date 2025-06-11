# highlight-start
from dagster_cloud.dagster_insights import (
    InsightsSnowflakeResource,
    create_snowflake_insights_asset_and_schedule,
)

# highlight-end
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
# highlight-end