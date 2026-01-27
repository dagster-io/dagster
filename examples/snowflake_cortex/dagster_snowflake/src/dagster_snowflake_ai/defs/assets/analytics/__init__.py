"""Analytics assets for partitioned data processing."""

from dagster_snowflake_ai.defs.assets.analytics.optimized_queries import (
    optimized_query_example,
    query_cost_tracking,
)
from dagster_snowflake_ai.defs.assets.analytics.partitioned_analytics import (
    daily_entity_summary,
    daily_sentiment_aggregates,
)

__all__ = [
    "daily_sentiment_aggregates",
    "daily_entity_summary",
    "optimized_query_example",
    "query_cost_tracking",
]
