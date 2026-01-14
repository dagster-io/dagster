"""Dagster assets for Snowflake AI integration."""

import dagster as dg

from dagster_snowflake_ai.defs.assets.analytics import partitioned_analytics
from dagster_snowflake_ai.defs.assets.cortex_ai import (
    aggregations,
    data_engineering_stories,
    entity_extraction,
    sentiment_analysis,
)
from dagster_snowflake_ai.defs.assets.dynamic_tables import dynamic_table_assets
from dagster_snowflake_ai.defs.assets.ingestion import stories, web_scraper
from dagster_snowflake_ai.defs.dbt import dbt_transform_assets

all_assets = dg.load_assets_from_modules(
    [
        stories,
        web_scraper,
        sentiment_analysis,
        entity_extraction,
        aggregations,
        data_engineering_stories,
        partitioned_analytics,
    ]
)

__all__ = ["all_assets", "dbt_transform_assets", "dynamic_table_assets"]
