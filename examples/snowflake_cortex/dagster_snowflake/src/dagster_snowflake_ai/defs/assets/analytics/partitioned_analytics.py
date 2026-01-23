"""Partitioned analytics assets for daily aggregations."""

import dagster as dg
from dagster_snowflake import SnowflakeResource

from dagster_snowflake_ai.defs.partitions import daily_partitions
from dagster_snowflake_ai.defs.resources import get_snowflake_connection_with_schema


@dg.asset(
    group_name="analytics",
    description="Daily sentiment aggregates partitioned by date",
    compute_kind="snowflake",
    partitions_def=daily_partitions,
    deps=["story_sentiment_analysis"],
)
def daily_sentiment_aggregates(
    context: dg.AssetExecutionContext,
    snowflake: SnowflakeResource,
) -> dg.MaterializeResult:
    """
    Aggregate sentiment analysis results by day.

    Creates daily aggregates from sentiment analysis table, showing:
    - Total stories per sentiment category
    - Stories by topic category
    - Data engineering story counts
    - Average description lengths

    Uses MERGE for incremental processing - only processes the partition date.
    """
    partition_date = context.partition_key

    with get_snowflake_connection_with_schema(snowflake) as (connection, schema):
        cursor = connection.cursor()  # type: ignore[attr-defined]

        # Create table if it doesn't exist
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {schema}.daily_sentiment_aggregates (
                report_date DATE PRIMARY KEY,
                total_stories INT,
                positive_count INT,
                neutral_count INT,
                negative_count INT,
                data_engineering_count INT,
                avg_description_length FLOAT,
                unique_posters INT,
                updated_at TIMESTAMP_NTZ
            )
        """)

        # Aggregate sentiment data for this partition
        cursor.execute(
            f"""
            MERGE INTO {schema}.daily_sentiment_aggregates AS target
            USING (
                SELECT
                    DATE(posted_at) as report_date,
                    COUNT(*) as total_stories,
                    COUNT_IF(sentiment_classification = 'positive') as positive_count,
                    COUNT_IF(sentiment_classification = 'neutral') as neutral_count,
                    COUNT_IF(sentiment_classification = 'negative') as negative_count,
                    COUNT_IF(is_data_engineering = 'data_engineering') as data_engineering_count,
                    AVG(LENGTH(COALESCE(description, title))) as avg_description_length,
                    COUNT(DISTINCT posted_by) as unique_posters,
                    CURRENT_TIMESTAMP() as updated_at
                FROM {schema}.story_sentiment
                WHERE DATE(posted_at) = %(partition_date)s
                GROUP BY DATE(posted_at)
            ) AS source
            ON target.report_date = source.report_date
            WHEN MATCHED THEN
                UPDATE SET
                    total_stories = source.total_stories,
                    positive_count = source.positive_count,
                    neutral_count = source.neutral_count,
                    negative_count = source.negative_count,
                    data_engineering_count = source.data_engineering_count,
                    avg_description_length = source.avg_description_length,
                    unique_posters = source.unique_posters,
                    updated_at = source.updated_at
            WHEN NOT MATCHED THEN
                INSERT (
                    report_date, total_stories, positive_count, neutral_count,
                    negative_count, data_engineering_count, avg_description_length,
                    unique_posters, updated_at
                )
                VALUES (
                    source.report_date, source.total_stories, source.positive_count,
                    source.neutral_count, source.negative_count, source.data_engineering_count,
                    source.avg_description_length, source.unique_posters, source.updated_at
                )
        """,
            {"partition_date": partition_date},
        )

        # Get aggregated stats
        cursor.execute(
            f"""
            SELECT
                total_stories,
                positive_count,
                neutral_count,
                negative_count,
                data_engineering_count,
                avg_description_length,
                unique_posters
            FROM {schema}.daily_sentiment_aggregates
            WHERE report_date = %(partition_date)s
        """,
            {"partition_date": partition_date},
        )
        result = cursor.fetchone()

        if result:
            (
                total_stories,
                positive_count,
                neutral_count,
                negative_count,
                data_engineering_count,
                avg_description_length,
                unique_posters,
            ) = result
        else:
            total_stories = 0
            positive_count = 0
            neutral_count = 0
            negative_count = 0
            data_engineering_count = 0
            avg_description_length = 0.0
            unique_posters = 0

        context.log.info(
            f"Daily sentiment aggregates for {partition_date}: "
            f"{total_stories} stories, {data_engineering_count} data engineering stories"
        )

    return dg.MaterializeResult(
        metadata={
            "partition_date": dg.MetadataValue.text(partition_date),
            "total_stories": dg.MetadataValue.int(total_stories),
            "positive_count": dg.MetadataValue.int(positive_count),
            "neutral_count": dg.MetadataValue.int(neutral_count),
            "negative_count": dg.MetadataValue.int(negative_count),
            "data_engineering_count": dg.MetadataValue.int(data_engineering_count),
            "avg_description_length": dg.MetadataValue.float(
                float(avg_description_length) if avg_description_length else 0.0
            ),
            "unique_posters": dg.MetadataValue.int(unique_posters),
        }
    )


@dg.asset(
    group_name="analytics",
    description="Daily entity extraction summaries partitioned by date",
    compute_kind="snowflake",
    partitions_def=daily_partitions,
    deps=["entity_extraction"],
)
def daily_entity_summary(
    context: dg.AssetExecutionContext,
    snowflake: SnowflakeResource,
) -> dg.MaterializeResult:
    """
    Summarize entity extraction results by day.

    Creates daily summaries from entity extraction table, showing:
    - Stories with extracted entities
    - Stories with company mentions
    - Stories with skill mentions
    - Stories with compensation info

    Uses MERGE for incremental processing - only processes the partition date.
    """
    partition_date = context.partition_key

    with get_snowflake_connection_with_schema(snowflake) as (connection, schema):
        cursor = connection.cursor()  # type: ignore[attr-defined]

        # Create table if it doesn't exist
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {schema}.daily_entity_summary (
                report_date DATE PRIMARY KEY,
                total_stories INT,
                stories_with_companies INT,
                stories_with_skills INT,
                stories_with_compensation INT,
                stories_with_experience INT,
                updated_at TIMESTAMP_NTZ
            )
        """)

        # Aggregate entity data for this partition
        cursor.execute(
            f"""
            MERGE INTO {schema}.daily_entity_summary AS target
            USING (
                SELECT
                    DATE(js.posted_at) as report_date,
                    COUNT(*) as total_stories,
                    COUNT_IF(e.company_names IS NOT NULL AND e.company_names != '') as stories_with_companies,
                    COUNT_IF(e.required_skills IS NOT NULL AND e.required_skills != '') as stories_with_skills,
                    COUNT_IF(e.compensation_info IS NOT NULL AND e.compensation_info != '') as stories_with_compensation,
                    COUNT_IF(e.experience_requirements IS NOT NULL AND e.experience_requirements != '') as stories_with_experience,
                    CURRENT_TIMESTAMP() as updated_at
                FROM {schema}.extracted_entities e
                JOIN {schema}.story_sentiment js ON e.job_id = js.job_id
                WHERE DATE(js.posted_at) = %(partition_date)s
                GROUP BY DATE(js.posted_at)
            ) AS source
            ON target.report_date = source.report_date
            WHEN MATCHED THEN
                UPDATE SET
                    total_stories = source.total_stories,
                    stories_with_companies = source.stories_with_companies,
                    stories_with_skills = source.stories_with_skills,
                    stories_with_compensation = source.stories_with_compensation,
                    stories_with_experience = source.stories_with_experience,
                    updated_at = source.updated_at
            WHEN NOT MATCHED THEN
                INSERT (
                    report_date, total_stories, stories_with_companies,
                    stories_with_skills, stories_with_compensation,
                    stories_with_experience, updated_at
                )
                VALUES (
                    source.report_date, source.total_stories, source.stories_with_companies,
                    source.stories_with_skills, source.stories_with_compensation,
                    source.stories_with_experience, source.updated_at
                )
        """,
            {"partition_date": partition_date},
        )

        # Get aggregated stats
        cursor.execute(
            f"""
            SELECT
                total_stories,
                stories_with_companies,
                stories_with_skills,
                stories_with_compensation,
                stories_with_experience
            FROM {schema}.daily_entity_summary
            WHERE report_date = %(partition_date)s
        """,
            {"partition_date": partition_date},
        )
        result = cursor.fetchone()

        if result:
            (
                total_stories,
                stories_with_companies,
                stories_with_skills,
                stories_with_compensation,
                stories_with_experience,
            ) = result
        else:
            total_stories = 0
            stories_with_companies = 0
            stories_with_skills = 0
            stories_with_compensation = 0
            stories_with_experience = 0

        context.log.info(
            f"Daily entity summary for {partition_date}: "
            f"{total_stories} stories, {stories_with_skills} with skills"
        )

    return dg.MaterializeResult(
        metadata={
            "partition_date": dg.MetadataValue.text(partition_date),
            "total_stories": dg.MetadataValue.int(total_stories),
            "stories_with_companies": dg.MetadataValue.int(stories_with_companies),
            "stories_with_skills": dg.MetadataValue.int(stories_with_skills),
            "stories_with_compensation": dg.MetadataValue.int(
                stories_with_compensation
            ),
            "stories_with_experience": dg.MetadataValue.int(stories_with_experience),
        }
    )
