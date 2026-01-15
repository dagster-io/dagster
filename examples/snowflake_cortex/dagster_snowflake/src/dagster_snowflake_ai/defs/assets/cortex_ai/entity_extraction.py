"""Entity extraction using Cortex COMPLETE."""

import dagster as dg
from dagster_snowflake import SnowflakeResource

from dagster_snowflake_ai.defs.resources import get_snowflake_connection_with_schema


@dg.asset(
    group_name="cortex_ai",
    description="Extract entities from stories using Cortex COMPLETE",
    compute_kind="snowflake",
    deps=["story_sentiment_analysis"],
)
def entity_extraction(
    context: dg.AssetExecutionContext,
    snowflake: SnowflakeResource,
) -> dg.MaterializeResult:
    """
    Use Cortex COMPLETE to extract structured entities from stories.

    Uses SNOWFLAKE.CORTEX.COMPLETE with custom prompts for:
    - Finding company names and organizations mentioned
    - Extracting technical topics and technologies discussed
    - Identifying data engineering related content

    Processes all stories from the sentiment analysis table.
    """
    with get_snowflake_connection_with_schema(snowflake) as (connection, schema):
        cursor = connection.cursor()  # type: ignore[attr-defined]

        cursor.execute(f"""
            CREATE OR REPLACE TABLE {schema}.extracted_entities AS
            SELECT
                job_id,
                title,
                SNOWFLAKE.CORTEX.COMPLETE(
                    'llama3.1-8b',
                    'Extract all company names and organizations mentioned in the following story. Return as a JSON array of strings. Text: ' || COALESCE(description, title, '')
                ) as company_names,
                SNOWFLAKE.CORTEX.COMPLETE(
                    'llama3.1-8b',
                    'Extract any financial information, funding amounts, valuations, or business metrics mentioned in the following story. Return as a JSON array of strings. Text: ' || COALESCE(description, title, '')
                ) as compensation_info,
                SNOWFLAKE.CORTEX.COMPLETE(
                    'llama3.1-8b',
                    'Extract data engineering skills, technologies, and tools mentioned in the following story. Focus on: Python, SQL, Spark, Airflow, Dagster, dbt, Snowflake, AWS, GCP, Azure, ETL, data pipelines, data warehouses, and similar data engineering technologies. Return as a JSON array of strings. Text: ' || COALESCE(description, title, '')
                ) as required_skills,
                SNOWFLAKE.CORTEX.COMPLETE(
                    'llama3.1-8b',
                    'Extract any experience levels, expertise requirements, or technical depth mentioned in the following story. Return as a JSON array of strings. Text: ' || COALESCE(description, title, '')
                ) as experience_requirements,
                sentiment_classification,
                story_category,
                is_data_engineering
            FROM {schema}.story_sentiment
        """)

        cursor.execute(f"""
            SELECT
                COUNT(*) as total_stories
            FROM {schema}.extracted_entities
        """)
        entity_statistics = cursor.fetchone()

        total_stories = entity_statistics[0] if entity_statistics else 0

    return dg.MaterializeResult(
        metadata={
            "stories_with_entities": dg.MetadataValue.int(total_stories),
            "model_used": dg.MetadataValue.text("llama3.1-8b"),
            "cortex_function": dg.MetadataValue.text("SNOWFLAKE.CORTEX.COMPLETE"),
        }
    )
