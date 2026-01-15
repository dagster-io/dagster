"""Hacker News stories ingestion assets."""

from datetime import datetime, timezone

import dagster as dg
from dagster_snowflake import SnowflakeResource

from dagster_snowflake_ai.defs.constants import (
    DEFAULT_HACKER_NEWS_MAX_STORIES,
    MAX_CONTENT_LENGTH,
    MAX_HEADLINE_LENGTH,
)
from dagster_snowflake_ai.defs.resources import (
    WebScraperResource,
    get_snowflake_connection_with_schema,
)
from dagster_snowflake_ai.utils.timezone_helpers import (
    parse_relative_time_with_tz,
    snowflake_timestamp,
)


@dg.asset(
    group_name="ingestion",
    description="Ingest raw stories from Hacker News",
    compute_kind="snowflake",
)
def raw_stories(
    context: dg.AssetExecutionContext,
    snowflake: SnowflakeResource,
    web_scraper: WebScraperResource,
) -> dg.MaterializeResult:
    """
    Ingest raw stories from Hacker News main feed into staging table.

    Fetches stories from Hacker News main feed and stores them in Snowflake.
    Uses MERGE to handle deduplication based on story_id.
    """
    with get_snowflake_connection_with_schema(snowflake) as (connection, schema):
        cursor = connection.cursor()  # type: ignore[attr-defined]

        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {schema}.stories (
                job_id VARCHAR(255) PRIMARY KEY,
                job_number VARCHAR(50),
                title VARCHAR(1000),
                description VARCHAR(100000),
                url VARCHAR(2000),
                posted_by VARCHAR(255),
                posted_at TIMESTAMP_NTZ,
                source VARCHAR(255),
                processed_at TIMESTAMP_NTZ
            )
        """)

        context.log.info(
            f"Fetching stories from Hacker News API "
            f"(max_stories={DEFAULT_HACKER_NEWS_MAX_STORIES})..."
        )
        stories = web_scraper.fetch_hackernews_stories(
            max_stories=DEFAULT_HACKER_NEWS_MAX_STORIES,
            story_type="top",
            context=context,
        )

        context.log.info(f"Fetched {len(stories)} total stories from Hacker News API")

        cursor.execute(f"SELECT COUNT(*) FROM {schema}.stories")
        count_before_result = cursor.fetchone()
        count_before = count_before_result[0] if count_before_result else 0

        stories_processed = 0

        for story in stories:
            story_id = story.get("story_id") or str(abs(hash(story.get("url", ""))))
            if not story_id:
                continue

            rank = story.get("rank", "")
            title = story.get("title", "")
            url = story.get("url", "")
            posted_by = story.get("author") or story.get("domain", "")
            time_posted = story.get("time_posted", "")
            story_text = story.get("text", "")

            posted_at = None
            if time_posted:
                try:
                    posted_at_tz = parse_relative_time_with_tz(time_posted)
                    posted_at = snowflake_timestamp(posted_at_tz)
                except (ValueError, TypeError) as exc:
                    context.log.warning(
                        f"Failed to parse time_posted '{time_posted}': {exc}"
                    )

            if not posted_at:
                posted_at = snowflake_timestamp(datetime.now(timezone.utc))

            source = "hackernews"
            # Use story text if available (self-posts), otherwise use title as description
            # The scraped_story_content asset will later populate this with full content for external URLs
            description = story_text if story_text else title

            cursor.execute(
                f"""
                MERGE INTO {schema}.stories AS target
                USING (
                    SELECT
                        %(job_id)s AS job_id,
                        %(job_number)s AS job_number,
                        %(title)s AS title,
                        %(description)s AS description,
                        %(url)s AS url,
                        %(posted_by)s AS posted_by,
                        %(posted_at)s AS posted_at,
                        %(source)s AS source,
                        CURRENT_TIMESTAMP() AS processed_at
                ) AS source
                ON target.job_id = source.job_id
                WHEN MATCHED THEN
                    UPDATE SET
                        job_number = source.job_number,
                        title = source.title,
                        description = source.description,
                        url = source.url,
                        posted_by = source.posted_by,
                        posted_at = source.posted_at,
                        source = source.source,
                        processed_at = source.processed_at
                WHEN NOT MATCHED THEN
                    INSERT (job_id, job_number, title, description, url, posted_by, posted_at, source, processed_at)
                    VALUES (source.job_id, source.job_number, source.title, source.description, source.url,
                            source.posted_by, source.posted_at, source.source, source.processed_at)
            """,
                {
                    "job_id": story_id,
                    "job_number": rank,
                    "title": title[:MAX_HEADLINE_LENGTH] if title else None,
                    "description": description[:MAX_CONTENT_LENGTH]
                    if description
                    else None,
                    "url": url[:2000] if url else None,
                    "posted_by": posted_by,
                    "posted_at": posted_at,
                    "source": source,
                },
            )

            stories_processed += 1

        cursor.execute(f"SELECT COUNT(*) FROM {schema}.stories")
        count_after_result = cursor.fetchone()
        count_after = count_after_result[0] if count_after_result else 0
        new_stories = count_after - count_before

        context.log.info(
            f"Processed {stories_processed} stories from Hacker News. "
            f"New stories added: {new_stories}. "
            f"Total stories in table: {count_after}"
        )

    return dg.MaterializeResult(
        metadata={
            "stories_processed": dg.MetadataValue.int(stories_processed),
            "new_stories_added": dg.MetadataValue.int(new_stories),
            "stories_in_staging": dg.MetadataValue.int(count_after),
            "total_stories_fetched": dg.MetadataValue.int(len(stories)),
            "table_schema": dg.MetadataValue.text(f"{schema}.stories"),
            "source": dg.MetadataValue.text("hackernews"),
        }
    )
