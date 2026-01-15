"""Job definitions for Dagster."""

import dagster as dg

daily_intelligence_job = dg.define_asset_job(
    name="daily_intelligence",
    selection=dg.AssetSelection.groups("ingestion", "cortex_ai"),
    description="Daily Hacker News processing using Cortex AI",
)

dbt_transform_job = dg.define_asset_job(
    name="dbt_transform",
    selection=dg.AssetSelection.groups("default"),
    description="Run dbt transformations on Snowflake data",
)

weekly_reports_job = dg.define_asset_job(
    name="weekly_reports",
    selection=dg.AssetSelection.all(),
    description="Weekly comprehensive Hacker News reports",
)
