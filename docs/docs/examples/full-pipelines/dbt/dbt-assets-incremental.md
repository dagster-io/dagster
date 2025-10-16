---
title: Adjust dbt asset config for incremental models
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

## 1. Include a template var

The first step is to add a new [template var](/guides/build/components/building-pipelines-with-components/using-template-variables) to your component. This will be used to define the partitions definition that will be used to partition the assets.

<CodeExample
  path="docs_projects/project_dbt/src/project_dbt/defs/transform/template_vars.py"
  language="python"
  title="src/project_dbt/defs/transform/template_vars.py"
/>

## 2. Update dbt component configuration

The next step is to update the `defs.yaml` file to use the new template var and apply this partitions definition to all assets using the `post_process` field:

<CodeExample
  path="docs_projects/project_dbt/src/project_dbt/defs/transform/_defs.yaml"
  language="yaml"
  title="src/project_dbt/defs/transform/defs.yaml"
/>

Finally, we need to pass in new configuration to the `cli_args` field so that the dbt execution actually changes based on what partition is executing. In particular, we want to pass in values to the `--vars` configuration field that determine the range of time that our incremental models should process.

When the `cli_args` field is resolved, it has access to a `context.partition_time_window` object, which is Dagster's representation of the time range that should be processed on the current run. This can be converted into a format recognized by your dbt project using template variables:

<CodeExample
  path="docs_projects/project_dbt/src/project_dbt/defs/transform/defs.yaml"
  language="yaml"
  title="src/project_dbt/defs/transform/defs.yaml"
/>

This design lets us:

- Automatically configure incremental filters with partition context.
- Keep partitioning consistent across upstream and downstream assets.
- Run incremental updates or full backfills as needed.

Best of all, this pattern applies automatically to every dbt model in the project. As you add more models — incremental or not — Dagster will handle them the same way, with no extra structural changes.

## Next steps

- Continue this example with [dbt tests](/examples/full-pipelines/dbt/dbt-tests).
