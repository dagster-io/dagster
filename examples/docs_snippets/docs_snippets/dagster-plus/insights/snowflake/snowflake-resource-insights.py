# highlight-start
from dagster_cloud.dagster_insights import InsightsSnowflakeResource

# highlight-end
import dagster as dg


# highlight-start
@dg.definitions
def resources() -> dg.Definitions:
    return dg.Definitions(
        resources={
            "snowflake": InsightsSnowflakeResource(
                user=dg.EnvVar("SNOWFLAKE_USER"), password=dg.EnvVar("SNOWFLAKE_PASSWORD")
            ),
        }
    )
# highlight-end
