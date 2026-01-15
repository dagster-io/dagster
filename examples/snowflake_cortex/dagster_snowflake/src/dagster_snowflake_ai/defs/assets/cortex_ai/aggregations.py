"""Intelligent aggregations using Cortex AI_AGG."""

import dagster as dg
from dagster_snowflake import SnowflakeResource

from dagster_snowflake_ai.defs.resources import get_snowflake_connection_with_schema


@dg.asset(
    group_name="cortex_ai",
    description="Generate AI-powered Hacker News story summaries using AI_AGG",
    compute_kind="snowflake",
    deps=["entity_extraction"],
)
def daily_story_summary(
    context: dg.AssetExecutionContext,
    snowflake: SnowflakeResource,
) -> dg.MaterializeResult:
    """
    Use Cortex AI_AGG to intelligently aggregate insights across Hacker News stories.

    This aggregates all Hacker News stories into coherent summaries without moving data out of Snowflake.
    """
    with get_snowflake_connection_with_schema(snowflake) as (connection, schema):
        cursor = connection.cursor()  # type: ignore[attr-defined]

        cursor.execute(f"""
            CREATE OR REPLACE TABLE {schema}.daily_story_summary AS
            WITH story_summaries AS (
                SELECT
                    DATE(posted_at) as report_date,
                    story_category,
                    COALESCE(description, title) as story_content,
                    sentiment_classification
                FROM {schema}.story_sentiment
            )
            SELECT
                report_date,
                story_category,
                AI_AGG(
                    story_content,
                    'Synthesize these Hacker News stories into a 3-paragraph summary.
                     Include: (1) key topics and themes, (2) common technologies and tools discussed,
                     (3) trends and patterns. Be specific with numbers and names.'
                ) as story_summary,
                COUNT(*) as story_count,
                COUNT_IF(sentiment_classification = 'positive') as positive_count,
                COUNT_IF(sentiment_classification = 'negative') as negative_count
            FROM story_summaries
            GROUP BY report_date, story_category
        """)

        cursor.execute(f"SELECT COUNT(*) FROM {schema}.daily_story_summary")
        summary_count_result = cursor.fetchone()
        summary_count = summary_count_result[0] if summary_count_result else 0

    return dg.MaterializeResult(
        metadata={
            "summary_count": dg.MetadataValue.int(summary_count),
            "dagster_value": dg.MetadataValue.text(
                "Dagster orchestrates when this runs, tracks lineage to source data, "
                "and monitors for freshness - Cortex does the AI heavy lifting"
            ),
        }
    )
