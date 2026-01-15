"""Optimized query patterns for Snowflake performance and cost optimization."""

import dagster as dg
from dagster_snowflake import SnowflakeResource

from dagster_snowflake_ai.defs.resources import get_snowflake_connection_with_schema


@dg.asset(
    group_name="analytics",
    description="Example of optimized query patterns for Snowflake",
    compute_kind="snowflake",
    deps=["daily_sentiment_aggregates"],
)
def optimized_query_example(
    context: dg.AssetExecutionContext,
    snowflake: SnowflakeResource,
) -> dg.MaterializeResult:
    """
    Demonstrate optimized query patterns for Snowflake.

    Best practices shown:
    1. Column selection (avoid SELECT *)
    2. CTE patterns for reusability
    3. Efficient filtering and aggregation
    4. Query result caching strategies
    """
    with get_snowflake_connection_with_schema(snowflake) as (connection, schema):
        cursor = connection.cursor()  # type: ignore[attr-defined]

        # Example 1: Column selection optimization
        # Instead of SELECT *, select only needed columns
        cursor.execute(f"""
            CREATE OR REPLACE TABLE {schema}.optimized_example AS
            WITH filtered_data AS (
                -- CTE 1: Filter early to reduce data scanned
                SELECT
                    report_date,
                    total_stories,
                    data_engineering_count,
                    positive_count,
                    negative_count
                FROM {schema}.daily_sentiment_aggregates
                WHERE report_date >= DATEADD('day', -30, CURRENT_DATE())
            ),
            aggregated AS (
                -- CTE 2: Aggregate filtered data
                SELECT
                    DATE_TRUNC('week', report_date) as week_start,
                    SUM(total_stories) as weekly_stories,
                    SUM(data_engineering_count) as weekly_de_stories,
                    AVG(CAST(positive_count AS FLOAT) / NULLIF(total_stories, 0)) as avg_positive_ratio,
                    COUNT(*) as days_in_week
                FROM filtered_data
                GROUP BY DATE_TRUNC('week', report_date)
            )
            -- Final SELECT: Only columns needed for output
            SELECT
                week_start,
                weekly_stories,
                weekly_de_stories,
                avg_positive_ratio,
                days_in_week,
                CURRENT_TIMESTAMP() as computed_at
            FROM aggregated
            ORDER BY week_start DESC
        """)

        # Example 2: Query optimization metadata
        cursor.execute(f"""
            SELECT
                COUNT(*) as total_weeks,
                SUM(weekly_stories) as total_stories_aggregated,
                AVG(avg_positive_ratio) as overall_positive_ratio
            FROM {schema}.optimized_example
        """)
        stats = cursor.fetchone()

        total_weeks = stats[0] if stats and stats[0] is not None else 0
        total_stories = (
            stats[1] if stats and len(stats) > 1 and stats[1] is not None else 0
        )
        overall_ratio = (
            float(stats[2])
            if stats and len(stats) > 2 and stats[2] is not None
            else 0.0
        )

        context.log.info(
            f"Optimized query processed {total_weeks} weeks, "
            f"{total_stories} total stories, "
            f"{overall_ratio:.2%} positive ratio"
        )

    return dg.MaterializeResult(
        metadata={
            "total_weeks": dg.MetadataValue.int(total_weeks),
            "total_stories_aggregated": dg.MetadataValue.int(total_stories),
            "overall_positive_ratio": dg.MetadataValue.float(overall_ratio),
            "optimization_notes": dg.MetadataValue.text(
                "Query uses: column selection, CTEs, early filtering, and efficient aggregation"
            ),
        }
    )


@dg.asset(
    group_name="analytics",
    description="Cost tracking example using Snowflake query history",
    compute_kind="snowflake",
)
def query_cost_tracking(
    context: dg.AssetExecutionContext,
    snowflake: SnowflakeResource,
) -> dg.MaterializeResult:
    """
    Track query costs and performance metrics.

    Queries INFORMATION_SCHEMA.QUERY_HISTORY to get:
    - Warehouse credits used
    - Query execution time
    - Data scanned (bytes)
    - Query patterns for optimization
    """
    with get_snowflake_connection_with_schema(snowflake) as (connection, schema):
        cursor = connection.cursor()  # type: ignore[attr-defined]

        # Query recent query history for cost tracking
        cursor.execute("""
            SELECT
                QUERY_ID,
                QUERY_TEXT,
                EXECUTION_STATUS,
                TOTAL_ELAPSED_TIME / 1000 as execution_time_seconds,
                BYTES_SCANNED,
                BYTES_SPILLED_TO_LOCAL_STORAGE,
                BYTES_SPILLED_TO_REMOTE_STORAGE,
                PARTITIONS_SCANNED,
                PARTITIONS_TOTAL,
                WAREHOUSE_NAME,
                START_TIME
            FROM TABLE(INFORMATION_SCHEMA.QUERY_HISTORY(
                RESULT_LIMIT => 10,
                END_TIME_RANGE_START => DATEADD('hour', -1, CURRENT_TIMESTAMP())
            ))
            WHERE EXECUTION_STATUS = 'SUCCESS'
            ORDER BY START_TIME DESC
        """)
        query_history = cursor.fetchall()

        total_execution_time = sum(row[3] for row in query_history if row[3])
        total_bytes_scanned = sum(row[4] if row[4] else 0 for row in query_history)
        queries_tracked = len(query_history)

        context.log.info(
            f"Tracked {queries_tracked} queries: "
            f"{total_execution_time:.2f}s execution time, "
            f"{total_bytes_scanned / 1024 / 1024:.2f} MB scanned"
        )

    return dg.MaterializeResult(
        metadata={
            "queries_tracked": dg.MetadataValue.int(queries_tracked),
            "total_execution_time_seconds": dg.MetadataValue.float(
                total_execution_time
            ),
            "total_bytes_scanned": dg.MetadataValue.int(total_bytes_scanned),
            "cost_tracking_note": dg.MetadataValue.text(
                "Use INFORMATION_SCHEMA.QUERY_HISTORY to track warehouse costs and optimize queries"
            ),
        }
    )
