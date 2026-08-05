---
title: Automate downstream assets
description: Trigger downstream assets from a sensor when a Snowflake Dynamic Table actually refreshes
last_update:
  author: Dennis Hume
sidebar_position: 40
---

A common pattern in data science and ML pipelines is building feature aggregations or summary tables in Snowflake — customer lifetime value scores, daily revenue rollups — and then running downstream Python pipelines that consume them. With Snowflake Dynamic Tables as virtual assets, those aggregates exist in the lineage graph but Dagster never executes them. That creates a problem: how does your downstream pipeline know when to re-run?

## The wrong answer: trigger on source change

It's tempting to reach for `AutomationCondition.eager().resolve_through_virtual()` on the downstream asset. `resolve_through_virtual()` makes automation treat virtual assets as transparent, tracing the dependency chain _through_ the Dynamic Tables back to the real source data — so the downstream asset re-runs whenever a source table changes.

For a virtual asset that is a synchronous view instantly consistent with its source that's exactly right. But a Dynamic Table is not a view. It's an asynchronously-refreshed cache with a `TARGET_LAG`: Snowflake guarantees the data is _at most_ that stale, and refreshes on its own schedule. `daily_revenue_rollup` in this example has a `TARGET_LAG` of one hour.

The lesson generalizes: `resolve_through_virtual()` is correct when the virtual asset is instantly consistent with its source, and wrong when the virtual asset is an asynchronous cache. A Dynamic Table is the latter.

## The right answer: trigger on refresh completion

The downstream asset should run _after_ the Dynamic Table refreshes, not when the source changes. The signal for "a refresh landed" is `last_completed_refresh` advancing — which is exactly what the [freshness sensor](/examples/full-pipelines/snowflake-dynamic-tables/freshness-monitoring) already reads every tick.

So the downstream asset carries no automation condition at all. It expresses its dependency for lineage, and is triggered by the sensor:

<CodeExample
  path="docs_projects/project_snowflake_dynamic_tables/src/project_snowflake_dynamic_tables/defs/assets/analytics.py"
  language="python"
  startAfter="start_dashboard_asset"
  endBefore="end_dashboard_asset"
  title="project_snowflake_dynamic_tables/defs/assets/analytics.py"
/>

`deps=["customer_lifetime_value", "daily_revenue_rollup"]` expresses the correct logical dependency — the asset reads from both Dynamic Tables at runtime. `executive_dashboard_report` could just as easily be a feature store update, a model retraining job, or any pipeline that should respond to Snowflake-computed aggregates.

## The sensor as trigger

The [freshness sensor](/examples/full-pipelines/snowflake-dynamic-tables/freshness-monitoring) you built on the previous page does this job. It declares `asset_selection=AssetSelection.assets("executive_dashboard_report")`, and on each tick — the same tick that emits the freshness observations — it decides whether to request a dashboard run. Three details make this correct:

1. **Fire on refresh completion, not source change.** The trigger reads `last_completed_refresh` for each table. A run is requested only once that timestamp moves — meaning Snowflake has committed new data the dashboard can actually read.
2. **Cold-start gate.** A `NULL` `last_completed_refresh` means a table has never finished a refresh. Firing then would `SELECT` an empty table and go green on nothing — the exact failure mode of the eager approach. The sensor waits until _both_ tables have a non-null refresh timestamp before it will fire.
3. **Composite `run_key` for idempotency.** The two tables refresh at different cadences (one minute vs. one hour). The `run_key` is the combined `(clv_ts, rollup_ts)` state, so the dashboard fires whenever _either_ table advances, and a given combined state never triggers twice. The cursor stores the last-seen state to detect the advance.

The dashboard is eventually consistent across the two tables: after a source change it may reflect the freshly-refreshed `customer_lifetime_value` while `daily_revenue_rollup` is still catching up to its hourly target. That's inherent to running two async caches at different lags — there is no single moment when both atomically reflect one source change. The guarantee the sensor _does_ provide is the one that matters: the dashboard never reads pre-refresh data, and "green" means "reflects each Dynamic Table's latest _committed refresh_," not "reflects the latest _source row_."

## What you've built

With the virtual specs, the sensor, and the checks in place, you have the complete pattern for incorporating Snowflake-managed objects into a Dagster data platform: Snowflake handles computation and refresh; Dagster provides lineage, automation, and observability. Virtual assets are the bridge — they give Dagster enough information to model the graph and surface health signals without ever attempting to execute objects it doesn't control. And because automation is driven by _refresh completion_ rather than _source change_, downstream work never runs ahead of the data.

For more on virtual assets and the broader family of non-executable assets, see the [virtual assets guide](/guides/build/assets/virtual-assets).
