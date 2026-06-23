---
title: Monitor Dynamic Table freshness
description: Use a sensor and asset checks to track Snowflake Dynamic Table refresh health in Dagster
last_update:
  author: Dennis Hume
sidebar_position: 30
---

Because the Dynamic Tables are virtual — Dagster never executes them — their metadata timeline in the asset catalog never updates on its own. Two complementary tools close this gap: a sensor that continuously records refresh state as observations, and asset checks that give a structured pass/fail signal when a table's scheduling state is unhealthy.

This same sensor does double duty: the refresh state it reads here is also what drives downstream automation on the [next page](/examples/full-pipelines/snowflake-dynamic-tables/automation). Monitoring refresh state and _triggering_ on refresh completion are the same problem, so they live in one sensor.

## The freshness sensor

The sensor runs every 60 seconds, queries `information_schema.dynamic_tables`, and emits one `AssetObservation` per table:

<CodeExample
  path="docs_projects/project_snowflake_dynamic_tables/src/project_snowflake_dynamic_tables/defs/sensors.py"
  language="python"
  startAfter="start_freshness_sensor"
  endBefore="end_freshness_sensor"
  title="project_snowflake_dynamic_tables/defs/sensors.py"
/>

The sensor returns `SensorResult(asset_events=[...], ...)`. The `asset_events` carry the `AssetObservation` objects that populate each virtual asset's metadata timeline in the Dagster UI — `scheduling_state`, `last_completed_refresh`, and `seconds_since_refresh`. The `skip_reason` surfaces the freshness summary in the sensor tick history on ticks where no downstream run is requested.

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

This pairing matters for automation, too: a `FAILED` table's `last_completed_refresh` simply stops advancing, so the trigger logic on the next page naturally stops firing for it — while the check turns red to surface the failure. The two mechanisms compose without any special-case handling.

## Next steps

Continue this example by [automating downstream assets](/examples/full-pipelines/snowflake-dynamic-tables/automation).
