---
title: Automate downstream assets
description: Use resolve_through_virtual to trigger downstream assets when upstream source data changes
last_update:
  author: Dennis Hume
sidebar_position: 30
---

A common pattern in data science and ML pipelines is building feature aggregations or summary tables in Snowflake — customer lifetime value scores, daily revenue rollups — and then running downstream Python pipelines that consume them. With Snowflake Dynamic Tables as virtual assets, those aggregates exist in the lineage graph but Dagster never executes them. That creates a problem: how does your downstream pipeline know to re-run when source data changes?

`AutomationCondition.eager().resolve_through_virtual()` solves this. It makes automation conditions treat virtual assets as transparent, tracing the dependency chain through the Dynamic Tables all the way back to the real source data.

## The downstream asset

`executive_dashboard_report` is a Python asset that reads from both Dynamic Tables and produces a summary. It could just as easily be a feature store update, a model retraining job, or an ML pipeline trigger — anything that should respond to changes in Snowflake-computed aggregates:

<CodeExample
  path="docs_projects/project_snowflake_dynamic_tables/src/project_snowflake_dynamic_tables/defs/assets/analytics.py"
  language="python"
  startAfter="start_dashboard_asset"
  endBefore="end_dashboard_asset"
  title="project_snowflake_dynamic_tables/defs/assets/analytics.py"
/>

`deps=["customer_lifetime_value", "daily_revenue_rollup"]` expresses the correct logical dependency — the asset reads from the Dynamic Tables at runtime. `resolve_through_virtual()` on the automation condition is what makes the trigger chain work end-to-end:

1. `raw_orders` is materialized (or reports a materialization via the external asset event API)
2. Dagster evaluates automation conditions for all downstream assets
3. `resolve_through_virtual()` traverses through `customer_lifetime_value` and `daily_revenue_rollup` (both virtual) to find `raw_orders` as the real upstream
4. `executive_dashboard_report` is requested

## Next steps

Continue this example by adding [dynamic table freshness monitoring](/examples/full-pipelines/snowflake-dynamic-tables/freshness-monitoring).
