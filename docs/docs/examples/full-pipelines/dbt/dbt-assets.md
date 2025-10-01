---
title: Create dbt assets
description: Create dbt assets for dbt example project
last_update:
  author: Dennis Hume
sidebar_position: 40
---

When dbt executes commands, it does so at the project level. For example, running `dbt run` executes all models in the project. You can pass flags like `--select` to limit execution, but the default behavior treats the project as a single unit.

In Dagster, we take a different approach: each dbt model becomes its own asset. This lets us build a fine-grained dependency graph where each model is linked to its upstream and downstream assets across both dbt and non-dbt layers within the Dagster project.

## 1. Scaffold the dbt component definition

The best way to integrate a dbt project with Dagster is through the [dbt component](/integrations/libraries/dbt). This component turns a dbt project directory into a set of Dagster assets, one per model. You can scaffold it with `dg`:

<CliInvocationExample path="docs_projects/project_dbt/commands/dg-scaffold-dbt-component.txt" />

The generated YAML already points to the correct project path, so no edits are needed:

```yaml
type: dagster_dbt.DbtProjectComponent

attributes:
  project: '{{ project_root }}/src/project_dbt/analytics'
```

## 2. Customize the dbt model assets

By default, all dbt models are represented as assets, but the asset keys may not align with the rest of your Dagster project.

To fix this, we can add a `translation` section to the scaffolding. Translations let us customize the names of the assets created by the component:

```yaml
type: dagster_dbt.DbtProjectComponent

attributes:
  project: '{{ project_root }}/src/project_dbt/analytics'
  translation:
    key: 'taxi_{{ node.name }}'
    group_name: dbt
```

This preserves lineage and ensures proper dependency tracking. In this example, the translator prepends `taxi_` to all dbt source names, so source (`zones`) maps cleanly to the existing `taxi_zones` asset in Dagster.

## Next steps

- Continue this example with [dbt incremental assets](/examples/full-pipelines/dbt/dbt-assets-incremental).
