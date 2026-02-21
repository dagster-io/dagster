"""Web scraping assets for story content extraction."""

import dagster as dg
from dagster_snowflake import SnowflakeResource

from dagster_snowflake_ai.defs.constants import DEFAULT_SCRAPE_BATCH_SIZE
from dagster_snowflake_ai.defs.resources import (
    WebScraperResource,
    get_snowflake_connection_with_schema,
)


@dg.asset(
    group_name="ingestion",
    description="Scrape story content from URLs in stories",
    compute_kind="snowflake",
    deps=["raw_stories"],
)
def scraped_story_content(
    context: dg.AssetExecutionContext,
    snowflake: SnowflakeResource,
    web_scraper: WebScraperResource,
) -> dg.MaterializeResult:
    """
    Scrape story content from URLs stored in stories table.

    Updates stories that have URLs but haven't been scraped yet.
    Extracts main content from story pages and stores it in the description field.
    """
    with get_snowflake_connection_with_schema(snowflake) as (connection, schema):
        cursor = connection.cursor()  # type: ignore[attr-defined]

        try:
            cursor.execute(f"""
                ALTER TABLE {schema}.stories
                ADD COLUMN IF NOT EXISTS scraped_at TIMESTAMP_NTZ
            """)
        except Exception as exc:
            context.log.debug(
                f"Could not add scraped_at column (may already exist): {exc}"
            )

        cursor.execute(f"""
            SELECT job_id, url, title
            FROM {schema}.stories
            WHERE url IS NOT NULL
              AND url LIKE 'http%'
              AND scraped_at IS NULL
            LIMIT {DEFAULT_SCRAPE_BATCH_SIZE}
        """)
        stories_to_scrape = cursor.fetchall()

        if not stories_to_scrape:
            context.log.info("No stories to scrape")
            return dg.MaterializeResult(
                metadata={
                    "stories_scraped": dg.MetadataValue.int(0),
                    "stories_failed": dg.MetadataValue.int(0),
                }
            )

        context.log.info(f"Found {len(stories_to_scrape)} stories to scrape")

        stories_scraped = 0
        stories_failed = 0

        for story_id, url, title in stories_to_scrape:
            if not web_scraper.is_valid_url(url):
                context.log.warning(f"Invalid URL for story {story_id}: {url}")
                stories_failed += 1
                continue

            try:
                context.log.info(f"Scraping story {story_id}: {(title or '')[:50]}...")
                scraped_content = web_scraper.scrape(url)

                if scraped_content:
                    cursor.execute(
                        f"""
                        UPDATE {schema}.stories
                        SET description = %(scraped_content)s,
                            scraped_at = CURRENT_TIMESTAMP()
                        WHERE job_id = %(story_id)s
                    """,
                        {
                            "scraped_content": scraped_content,
                            "story_id": story_id,
                        },
                    )
                    stories_scraped += 1
                    context.log.info(f"Successfully scraped story {story_id}")
                else:
                    cursor.execute(
                        f"""
                        UPDATE {schema}.stories
                        SET scraped_at = CURRENT_TIMESTAMP()
                        WHERE job_id = %(story_id)s
                    """,
                        {"story_id": story_id},
                    )
                    stories_failed += 1
                    context.log.warning(
                        f"Failed to scrape content for story {story_id}"
                    )

            except Exception as exc:
                context.log.error(f"Error scraping story {story_id}: {exc}")
                stories_failed += 1
                try:
                    cursor.execute(
                        f"""
                        UPDATE {schema}.stories
                        SET scraped_at = CURRENT_TIMESTAMP()
                        WHERE job_id = %(story_id)s
                    """,
                        {"story_id": story_id},
                    )
                except Exception as update_exc:
                    context.log.error(
                        f"Failed to update scraped_at for story {story_id}: {update_exc}"
                    )

        context.log.info(
            f"Scraping complete: {stories_scraped} succeeded, {stories_failed} failed"
        )

    return dg.MaterializeResult(
        metadata={
            "stories_scraped": dg.MetadataValue.int(stories_scraped),
            "stories_failed": dg.MetadataValue.int(stories_failed),
            "total_processed": dg.MetadataValue.int(len(stories_to_scrape)),
        }
    )
