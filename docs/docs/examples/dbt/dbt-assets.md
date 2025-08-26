---
title: dbt assets
description: The dbt assets
last_update:
  author: Dennis Hume
sidebar_position: 40
---

When dbt executes commands, it does so at the project level. For example, running `dbt run` will execute all models within the project. You can use flags to run specific models or subsets—such as with `--select` but the default behavior treats the project as a monolithic unit.

Instead of taking that approach in Dagster, we’ll treat each dbt model as an individual asset. This allows us to build a fine-grained dependency graph, where each model is linked to its upstream and downstream assets, across both dbt and non-dbt layers, within our Dagster project.

## Parsing the dbt project

The best way to integrate a dbt project with Dagster is using the [dbt component](/integrations/libraries/dbt). This can turn a dbt project directory into a collection of assets for each model. We can do this with `dg` and scaffolding the component:

<CliInvocationExample path="docs_projects/project_dbt/commands/dg-scaffold-dbt-component.txt" />

There is no need to edit the scaffolding YAML at this point since the `dg` command generates the correct project path:

```yaml
type: dagster_dbt.DbtProjectComponent

attributes:
  project: '{{ project_root }}/src/project_dbt/analytics'
```

## Customizing assets

At this point all of the dbt models are represented as assets. However the asset keys do not line up correctly.

To solve this problem we can add a `translation` to the scaffolding. This translation allows us to modify the names of the assets we produce within the component:

```yaml
type: dagster_dbt.DbtProjectComponent

attributes:
  project: '{{ project_root }}/src/project_dbt/analytics'
  translation:
    key: 'taxi_{{ node.name }}'
    group_name: dbt
```

This maintains the proper lineage and ensures proper dependency tracking, the translator modifies source names, prepending `taxi_` to all dbt source names, so that source(`zones`) maps to the existing `taxi_zones` asset in Dagster.

## Incrementals

Now that lineage is set, there is one final change we need to make to our scaffolding. As previously mentioned, in our dbt project, the `daily_metrics` is an [incremental model](https://docs.getdbt.com/docs/build/incremental-models). Incremental models optimize performance by avoiding full refreshes, they process only new or modified data based on a time filter.

<CodeExample
  path="docs_projects/project_dbt/src/project_dbt/analytics/models/marts/daily_metrics.sql"
  language="sql"
  title="src/project_dbt/analytics/models/marts/daily_metrics.sql"
/>

Here's how it works:

- On the first run, the model runs without filters and processes the full dataset.
- On subsequent runs, dbt applies the `is_incremental()` filter, using `min_date` and `max_date` values that must be provided at runtime.

Since Dagster is executing dbt, we want Dagster to be responsible for passing the variables in the `is_incremental` function of the dbt model. These values will come from the context of the Dagster partition.

We can update the scaffolding YAML to account for partitions:

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
