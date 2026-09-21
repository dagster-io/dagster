---
title: dbt selectors with DbtProjectComponent
description: Workarounds, cross-code-location dependencies, and column lineage for using dbt selectors with DbtProjectComponent in Dagster+.
sidebar_position: 500
---

`DbtProjectComponent` does not directly accept dbt selectors through a dedicated `selector` parameter as of Dagster 1.12.0. The `@dbt_assets` decorator does support selectors. This guide covers four workarounds for `DbtProjectComponent`, plus related patterns for cross-code-location dependencies and column lineage.

## Workarounds for selector support

### 1. Use `@dbt_assets` with selectors (recommended)

When you need full dbt selector support, use the <PyObject section="libraries" integration="dbt" module="dagster_dbt" object="dbt_assets" decorator /> decorator instead of the component:

<CodeExample
  path="docs_snippets/docs_snippets/integrations/dbt/dbt_selectors.py"
  startAfter="start_dbt_assets_with_selector"
  endBefore="end_dbt_assets_with_selector"
  title="src/<project_name>/defs/dbt_assets.py"
/>

### 2. Use `select` and `exclude` with tags

`DbtProjectComponent` accepts `select` and `exclude` filters that mirror dbt's selection syntax. Tags work directly:

```yaml
# defs.yaml
type: dagster_dbt.DbtProjectComponent
attributes:
  project:
    project_dir: '{{ project_root }}/path/to/dbt_project'
  select: 'tag:my_tag'
  exclude: 'tag:exclude_tag'
```

### 3. Reference a dbt selector by tag

If you have a richer selector defined in `selectors.yml`, give the underlying models a tag and reference that tag from the component. The component does not read `selectors.yml` directly, but tag-based selection achieves equivalent results:

```yaml
# selectors.yml in your dbt project
selectors:
  - name: my_business_logic
    description: 'Core business models'
    definition:
      method: tag
      value: business_core
      children: true
```

```yaml
type: dagster_dbt.DbtProjectComponent
attributes:
  project:
    project_dir: '{{ project_root }}/dbt_project'
  select: 'tag:business_core'
```

### 4. Path-based selection

For directory-driven layouts (marts, staging, intermediate), select by path:

```yaml
type: dagster_dbt.DbtProjectComponent
attributes:
  project:
    project_dir: '{{ project_root }}/dbt_project'
  select: 'path:models/marts/'
  exclude: 'path:models/staging/'
```

## Cross-code-location dependencies

You can wire non-dbt assets in one code location into `DbtProjectComponent` assets in another by matching asset keys.

**Step 1:** Define the upstream ingestion asset:

<CodeExample
  path="docs_snippets/docs_snippets/integrations/dbt/dbt_selectors.py"
  startAfter="start_ingestion_asset"
  endBefore="end_ingestion_asset"
  title="src/<project_name>/defs/ingestion.py"
/>

**Step 2:** Declare the asset key on the dbt source:

```yaml
# sources.yml in your dbt project
sources:
  - name: my_ingestion
    tables:
      - name: my_table
        meta:
          dagster:
            asset_key: ['my_ingestion', 'my_table']
```

**Step 3:** Reference the source in your dbt model:

```sql
-- models/my_model.sql
select * from {{ source('my_ingestion', 'my_table') }}
```

Dagster establishes the dependency automatically based on the matching asset key, even though the upstream asset and the dbt model live in different code locations.

## Column lineage

Enable column metadata on the component to surface column-level lineage in Dagster+:

```yaml
type: dagster_dbt.DbtProjectComponent
attributes:
  project:
    project_dir: '{{ project_root }}/dbt_project'
  include_metadata:
    - column_metadata # Available in Dagster 1.11.13+
```

:::note

Column lineage appears after the dbt assets are materialized, not immediately on definition load.

:::

## Choosing between approaches

| Use case                     | Recommendation        | Reason                              |
| ---------------------------- | --------------------- | ----------------------------------- |
| Native dbt selectors         | `@dbt_assets`         | Full selector support               |
| Simple tag or path filtering | `DbtProjectComponent` | Easier configuration                |
| Cross-location dependencies  | Either                | Both work with proper source setup  |
| Large projects               | `DbtProjectComponent` | Modern approach, better performance |
| Complex customization        | `@dbt_assets`         | More flexibility                    |

## Roadmap

The Dagster team is closing the gap between `DbtProjectComponent` and `@dbt_assets` so the component eventually supports the full feature surface, including native selectors. Until then, the tag- and path-based approaches above provide equivalent functionality.

## Related documentation

- [Using dbt with Dagster+](/integrations/libraries/dbt/using-dbt-with-dagster-plus)
- [dbt patterns and best practices](/integrations/libraries/dbt/dbt-patterns)
- [DbtProjectComponent missing manifest.json error](/deployment/troubleshooting/dbtprojectcomponent-missing-manifest-json)
