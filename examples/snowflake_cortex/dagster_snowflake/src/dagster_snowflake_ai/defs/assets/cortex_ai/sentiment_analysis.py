"""Sentiment analysis using Cortex AI_CLASSIFY."""

import dagster as dg
from dagster_snowflake import SnowflakeResource

from dagster_snowflake_ai.defs.resources import get_snowflake_connection_with_schema


@dg.asset(
    group_name="cortex_ai",
    description="Analyze sentiment and categorize stories using Cortex AI_CLASSIFY",
    compute_kind="snowflake",
    metadata={
        "cortex_function": "AI_CLASSIFY",
        "model": "snowflake-arctic",
    },
    deps=["scraped_story_content"],
)
def story_sentiment_analysis(
    context: dg.AssetExecutionContext,
    snowflake: SnowflakeResource,
) -> dg.MaterializeResult:
    """
    Use Cortex AI_CLASSIFY to categorize story sentiment and topics.

    This demonstrates:
    - AI inference directly in SQL (no data movement)
    - Batch processing at scale
    - Dagster tracking AI workload costs
    """
    with get_snowflake_connection_with_schema(snowflake) as (connection, schema):
        cursor = connection.cursor()  # type: ignore[attr-defined]

        # Optimized query: Select only needed columns and use CTE for reusability
        cursor.execute(f"""
            CREATE OR REPLACE TABLE {schema}.story_sentiment AS
            WITH story_content AS (
                -- CTE: Extract only needed columns and prepare content
                SELECT
                    job_id,
                    title,
                    description,
                    url,
                    posted_by,
                    posted_at,
                    source,
                    COALESCE(description, title) as content_for_analysis
                FROM {schema}.stories
                WHERE description IS NOT NULL OR title IS NOT NULL
            )
            SELECT
                -- Select only columns needed downstream (avoid SELECT *)
                job_id,
                title,
                description,
                url,
                posted_by,
                posted_at,
                source,
                -- AI classifications (reuse content_for_analysis from CTE)
                AI_CLASSIFY(
                    content_for_analysis,
                    ARRAY_CONSTRUCT('positive', 'neutral', 'negative')
                ):class::STRING as sentiment_classification,
                AI_CLASSIFY(
                    content_for_analysis,
                    ARRAY_CONSTRUCT('technology', 'startup', 'programming', 'ai_ml', 'web_development', 'mobile', 'devops', 'security', 'business', 'science', 'other')
                ):class::STRING as story_category,
                AI_CLASSIFY(
                    content_for_analysis,
                    ARRAY_CONSTRUCT('data_engineering', 'not_data_engineering')
                ):class::STRING as is_data_engineering,
                CURRENT_TIMESTAMP() as analyzed_at
            FROM story_content
            ORDER BY posted_at DESC
        """)

        cursor.execute(f"""
            SELECT
                COUNT(*) as stories_processed,
                COUNT(DISTINCT posted_by) as unique_posters,
                AVG(LENGTH(COALESCE(description, title))) as avg_description_length,
                COUNT_IF(is_data_engineering = 'data_engineering') as data_engineering_stories
            FROM {schema}.story_sentiment
        """)
        processing_statistics = cursor.fetchone()

        stories_processed = processing_statistics[0] if processing_statistics else 0
        unique_posters = processing_statistics[1] if processing_statistics else 0
        avg_description_length = (
            float(processing_statistics[2])
            if processing_statistics and processing_statistics[2]
            else 0.0
        )
        data_engineering_stories = (
            processing_statistics[3]
            if processing_statistics and len(processing_statistics) > 3
            else 0
        )

    return dg.MaterializeResult(
        metadata={
            "stories_processed": dg.MetadataValue.int(stories_processed),
            "data_engineering_stories": dg.MetadataValue.int(data_engineering_stories),
            "unique_posters": dg.MetadataValue.int(unique_posters),
            "avg_description_length": dg.MetadataValue.float(avg_description_length),
            "cortex_function": dg.MetadataValue.text("AI_CLASSIFY"),
            "dagster_insight": dg.MetadataValue.text(
                "Track this asset's Cortex compute costs in Dagster Insights"
            ),
        }
    )
