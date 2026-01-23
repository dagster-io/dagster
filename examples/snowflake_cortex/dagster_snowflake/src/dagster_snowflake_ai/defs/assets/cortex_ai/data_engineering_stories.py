"""Data engineering stories analysis."""

import dagster as dg
from dagster_snowflake import SnowflakeResource

from dagster_snowflake_ai.defs.resources import get_snowflake_connection_with_schema


@dg.asset(
    group_name="cortex_ai",
    description="Filter and analyze data engineering related stories from Hacker News",
    compute_kind="snowflake",
    deps=["entity_extraction"],
)
def data_engineering_stories(
    context: dg.AssetExecutionContext,
    snowflake: SnowflakeResource,
) -> dg.MaterializeResult:
    """
    Extract and analyze data engineering related stories specifically.

    Filters stories to focus on data engineering topics and extracts:
    - Company names and organizations mentioned
    - Data engineering skills and technologies discussed (Python, SQL, Spark, Airflow, Dagster, dbt, etc.)
    - Technical information and metrics
    - Experience and expertise levels mentioned
    """
    with get_snowflake_connection_with_schema(snowflake) as (connection, schema):
        cursor = connection.cursor()  # type: ignore[attr-defined]

        cursor.execute(f"""
            CREATE OR REPLACE TABLE {schema}.data_engineering_stories AS
            SELECT
                e.job_id,
                e.title,
                js.description,
                js.url,
                js.posted_by,
                js.posted_at,
                js.story_category,
                e.company_names,
                e.compensation_info,
                e.required_skills,
                e.experience_requirements,
                js.sentiment_classification
            FROM {schema}.extracted_entities e
            JOIN {schema}.story_sentiment js ON e.job_id = js.job_id
            WHERE js.is_data_engineering = 'data_engineering'
            ORDER BY js.posted_at DESC
        """)

        cursor.execute(f"""
            SELECT
                COUNT(*) as total_data_engineering_stories,
                COUNT(DISTINCT posted_by) as unique_authors,
                COUNT_IF(url IS NOT NULL) as stories_with_urls,
                COUNT_IF(compensation_info IS NOT NULL) as stories_with_metrics
            FROM {schema}.data_engineering_stories
        """)
        stats = cursor.fetchone()

        total_stories = stats[0] if stats else 0
        unique_authors = stats[1] if stats and len(stats) > 1 else 0
        stories_with_urls = stats[2] if stats and len(stats) > 2 else 0
        stories_with_metrics = stats[3] if stats and len(stats) > 3 else 0

        cursor.execute(f"""
            SELECT
                COUNT(*) as stories_count
            FROM {schema}.data_engineering_stories
            WHERE required_skills IS NOT NULL
        """)
        skills_result = cursor.fetchone()
        stories_with_skills = skills_result[0] if skills_result else 0

    return dg.MaterializeResult(
        metadata={
            "total_data_engineering_stories": dg.MetadataValue.int(total_stories),
            "unique_authors": dg.MetadataValue.int(unique_authors),
            "stories_with_urls": dg.MetadataValue.int(stories_with_urls),
            "stories_with_metrics": dg.MetadataValue.int(stories_with_metrics),
            "stories_with_skills": dg.MetadataValue.int(stories_with_skills),
            "focus": dg.MetadataValue.text("data_engineering_stories"),
        }
    )
