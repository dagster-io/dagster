---
title: dbt incremental assets
description: The dbt incremental assets
last_update:
  author: Dennis Hume
sidebar_position: 50
---

With lineage in place, there’s one final adjustment to make to our scaffolding. In our dbt project, the `daily_metrics` model is an [incremental model](https://docs.getdbt.com/docs/build/incremental-models). Incremental models improve performance by avoiding full refreshes: instead of reprocessing everything, they only handle new or modified data based on a time filter.

<CodeExample
  path="docs_projects/project_dbt/src/project_dbt/analytics/models/marts/daily_metrics.sql"
  language="sql"
  title="src/project_dbt/analytics/models/marts/daily_metrics.sql"
/>

Here’s how incremental models work:

- **First run**: the model processes the full dataset with no filters.
- **Subsequent runs**: dbt applies the `is_incremental()` filter, using `min_date` and `max_date` values provided at runtime.

Since Dagster is orchestrating dbt, we want Dagster to supply those variables. The values come directly from the Dagster partition context.

To enable this, we update the scaffolding YAML to include partitions:

<CodeExample
  path="docs_projects/project_dbt/src/project_dbt/defs/transform/defs.yaml"
  language="yaml"
  title="src/project_dbt/defs/transform/defs.yaml"
/>

This design lets us:

- Automatically configure incremental filters with partition context.
- Keep partitioning consistent across upstream and downstream assets.
- Run incremental updates or full backfills as needed.

Best of all, this pattern applies automatically to every dbt model in the project. As you add more models—incremental or not—Dagster will handle them the same way, with no extra structural changes.

## Next steps

- Continue this example with [dbt tests](/examples/dbt/dbt-tests)
