---
title: dbt assets
description: The base dbt assets
last_update:
  author: Dennis Hume
sidebar_position: 40
---

When dbt executes commands, it does so at the project level. For example, running `dbt run` will execute all models within the project. You can use flags to run specific models or subsets—such as with `--select` but the default behavior treats the project as a monolithic unit.

Instead of taking that approach in Dagster, we’ll treat each dbt model as an individual asset. This allows us to build a fine-grained dependency graph, where each model is linked to its upstream and downstream assets, across both dbt and non-dbt layers, within our Dagster project.

## Parsing the dbt project

<CliInvocationExample path="docs_snippets/docs_snippets/guides/tutorials/dagster-tutorial/commands/dg-scaffold-dbt-component.txt" />

The first step in integrating dbt with Dagster is to parse the dbt project using the `DbtProject` object from the `dagster_dbt` library. You just need to provide the path to the dbt project directory:

```yaml
type: dagster_dbt.DbtProjectComponent

attributes:
  project: '{{ project_root }}/src/project_dbt/analytics'
```

Next, we set a translator to help Dagster align dbt models and sources with the appropriate Dagster asset keys. This is necessary because the naming in the dbt project may differ from the asset names used elsewhere in our pipeline:

| dbt Source | Asset Name   |
| ---------- | ------------ |
| `zones`    | `taxi_zones` |
| `trips`    | `taxi_trips` |

To maintain lineage and ensure proper dependency tracking, the translator modifies source names using the `get_asset_key` method. In this case, we prepend `taxi_` to all dbt source names, so that source(`zones`) maps to the existing `taxi_zones` asset in Dagster:

## Incrementals

However, there’s one piece of Dagster-specific logic we do need to introduce: support for incremental models:

<CodeExample
  path="docs_projects/project_dbt/src/project_dbt/analytics/models/marts/daily_metrics.sql"
  language="sql"
  title="src/project_dbt/analytics/models/marts/daily_metrics.sql"
/>


[dbt build](https://docs.getdbt.com/reference/commands/build)

```bash
dbt build --vars "{min_date: '{{ partition_key_range.start }}', max_date: '{{ partition_key_range.end }}'}"
```

In our dbt project, the `daily_metrics` is an [incremental model](https://docs.getdbt.com/docs/build/incremental-models). Incremental models optimize performance by avoiding full refreshes, they process only new or modified data based on a time filter.

Here's how it works:

- On the first run, the model runs without filters and processes the full dataset.
- On subsequent runs, dbt applies the `is_incremental()` filter, using `min_date` and `max_date` values that must be provided at runtime.

Since `daily_metrics` is downstream of our partitioned asset `taxi_trips`, we want to manage this temporal logic at the Dagster orchestration level, ensuring that each partitioned run provides the correct date boundaries:

<CodeExample
  path="docs_projects/project_dbt/src/project_dbt/defs/transform/defs.yaml"
  language="yaml"
  title="src/project_dbt/defs/transform/defs.yaml"
/>

This design allows us to:

- Automatically configure incremental filters using partition context.
- Maintain consistent partitioning across upstream and downstream assets.
- Execute incremental updates or full backfills with flexibility.

Best of all, this setup applies automatically to all dbt models in the project. If you add more models in the future, whether incremental or not, Dagster will handle them using the same pattern, with no need for structural changes.

## Next steps

- Continue this example with [dbt tests](/examples/dbt/dbt-tests)
