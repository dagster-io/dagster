---
title: Monitor Dynamic Table freshness
description: Use a sensor and asset checks to track Snowflake Dynamic Table refresh health in Dagster
last_update:
  author: Dennis Hume
sidebar_position: 40
---

Because the Dynamic Tables are virtual — Dagster never executes them — their metadata timeline in the asset catalog never updates on its own. Two complementary tools close this gap: a sensor that continuously records refresh state as observations, and asset checks that give a structured pass/fail signal when a table's scheduling state is unhealthy.

## The freshness sensor

The sensor runs every 60 seconds, queries `information_schema.dynamic_tables`, and emits one `AssetObservation` per table:

<CodeExample
  path="docs_projects/project_snowflake_dynamic_tables/src/project_snowflake_dynamic_tables/defs/sensors.py"
  language="python"
  startAfter="start_freshness_sensor"
  endBefore="end_freshness_sensor"
  title="project_snowflake_dynamic_tables/defs/sensors.py"
/>

The sensor returns `SensorResult(asset_events=[...], skip_reason="...")` rather than run requests. `asset_events` carries the `AssetObservation` objects that populate each virtual asset's metadata timeline in the Dagster UI. The `skip_reason` surfaces the freshness summary in the sensor tick history.

## Freshness checks on the virtual assets

Observations record state — they don't pass or fail. For a structured health signal, asset checks co-located with the virtual specs query `scheduling_state` and return a boolean result:

<CodeExample
  path="docs_projects/project_snowflake_dynamic_tables/src/project_snowflake_dynamic_tables/defs/assets/dynamic_tables.py"
  language="python"
  startAfter="start_freshness_checks"
  endBefore="end_freshness_checks"
  title="project_snowflake_dynamic_tables/defs/assets/dynamic_tables.py"
/>

The check passes when `scheduling_state` is `RUNNING` or `SUSPENDED` — both are valid healthy states for a Snowflake Dynamic Table. Any other state (e.g. `FAILED`) causes the check to fail, making the problem visible in the Dagster asset catalog as a failed check rather than requiring manual inspection of Snowflake.

## What you've built

With the sensor and checks in place, you have the complete pattern for incorporating Snowflake-managed objects into a Dagster data platform: Snowflake handles computation and refresh, Dagster provides lineage, automation, and observability. Virtual assets are the bridge — they give Dagster enough information to route automation correctly and surface health signals without ever attempting to execute objects it doesn't control.

For more on virtual assets and the broader family of non-executable assets, see the [virtual assets guide](/guides/build/assets/virtual-assets).
