import sys
from typing import Any

from dagster_cloud.dagster_insights.snowflake.dbt_wrapper import (
    dbt_with_snowflake_insights as dbt_with_snowflake_insights,
)
from dagster_cloud.dagster_insights.snowflake.definitions import (
    create_snowflake_insights_asset_and_schedule as create_snowflake_insights_asset_and_schedule,
)
from dagster_cloud.dagster_insights.snowflake.snowflake_utils import (
    meter_snowflake_query as meter_snowflake_query,
)

dagster_snowflake_req_imports = {"InsightsSnowflakeResource"}
try:
    from dagster_cloud.dagster_insights.snowflake.insights_snowflake_resource import (
        InsightsSnowflakeResource as InsightsSnowflakeResource,
    )
except ImportError:
    pass

dagster_bigquery_req_imports = {"InsightsBigQueryResource", "dbt_with_bigquery_insights"}
try:
    from dagster_cloud.dagster_insights.bigquery.dbt_wrapper import (
        dbt_with_bigquery_insights as dbt_with_bigquery_insights,
    )
    from dagster_cloud.dagster_insights.bigquery.insights_bigquery_resource import (
        InsightsBigQueryResource as InsightsBigQueryResource,
    )
except ImportError:
    pass


# This is overriden in order to provide a better error message
# when the user tries to import a symbol which relies on another integration
# being installed.
def __getattr__(name) -> Any:
    obj = sys.modules[__name__].__dict__.get(name)
    if not obj:
        if name in dagster_snowflake_req_imports:
            raise ImportError(
                f"You are trying to import {name}, but the "
                "dagster-snowflake library is not installed. You can install it with "
                "`pip install dagster-snowflake`.",
            )
        elif name in dagster_bigquery_req_imports:
            raise ImportError(
                f"You are trying to import {name}, but the "
                "dagster-gcp library is not installed. You can install it with "
                "`pip install dagster-gcp`.",
            )
        else:
            raise AttributeError(f"module {__name__} has no attribute {name}")
    return obj
