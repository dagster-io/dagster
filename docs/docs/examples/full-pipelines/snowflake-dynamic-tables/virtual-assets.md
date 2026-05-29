---
title: Define virtual assets
description: Declare Snowflake Dynamic Tables as virtual assets in Dagster for correct lineage without execution
last_update:
  author: Dennis Hume
sidebar_position: 20
---

When Snowflake manages your transformations — through Dynamic Tables, views, or other objects — Dagster should know they exist without trying to run them. The question is which of Dagster's two non-executable asset types is the right fit.

Both [external assets](/guides/build/assets/external-assets) and [virtual assets](/guides/build/assets/virtual-assets) appear in the lineage graph without being executed by Dagster. The difference is how automation treats them:

- **External assets** are opaque to automation conditions. Dagster sees them in the graph, but evaluating whether a change should trigger a downstream run requires an explicit event.
- **Virtual assets** are transparent. Automation conditions can look through them to their real upstream sources via `resolve_through_virtual()`, treating them like a synchronous view that is instantly consistent with its source.

[Snowflake Dynamic Tables](https://docs.snowflake.com/en/user-guide/dynamic-tables/overview) are a natural fit for virtual assets. They refresh automatically based on a target lag — Snowflake handles the computation, and Dagster should never run them. Declaring them with `is_virtual=True` models this correctly while keeping full lineage intact.

:::note A Dynamic Table is not a view

The transparency described above is ideal for _lineage_, but be careful with it for _automation_. A Dynamic Table isn't instantly consistent with its source. It refreshes asynchronously on a target lag. Triggering downstream work the moment the source changes would run ahead of the data. The [automation page](/examples/full-pipelines/snowflake-dynamic-tables/automation) covers why, and shows the correct trigger: fire on refresh _completion_, driven by the freshness sensor.

:::

## External source tables

The raw source tables — loaded by an external ETL pipeline — are represented as plain `AssetSpec` objects. Dagster tracks them for lineage but never executes them:

<CodeExample
  path="docs_projects/project_snowflake_dynamic_tables/src/project_snowflake_dynamic_tables/defs/assets/sources.py"
  language="python"
  startAfter="start_source_specs"
  endBefore="end_source_specs"
  title="project_snowflake_dynamic_tables/defs/assets/sources.py"
/>

## Snowflake Dynamic Tables as virtual assets

The Dynamic Tables are declared with `is_virtual=True`. They appear in the lineage graph and can be observed, but Dagster will never place them in a run:

<CodeExample
  path="docs_projects/project_snowflake_dynamic_tables/src/project_snowflake_dynamic_tables/defs/assets/dynamic_tables.py"
  language="python"
  startAfter="start_dynamic_table_specs"
  endBefore="end_dynamic_table_specs"
  title="project_snowflake_dynamic_tables/defs/assets/dynamic_tables.py"
/>

Key properties on each virtual spec:

- `is_virtual=True` — marks the asset as unexecutable
- `deps=[...]` — preserves lineage so automation can traverse from source tables through the Dynamic Tables to downstream assets
- `metadata` — stores Snowflake-specific properties (target lag, refresh mode, table name) visible in the asset catalog

## Next steps

Continue this example by [monitoring Dynamic Table freshness](/examples/full-pipelines/snowflake-dynamic-tables/freshness-monitoring).
