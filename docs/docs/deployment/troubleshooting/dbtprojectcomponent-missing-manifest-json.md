---
title: Deploying DbtProjectComponent to Dagster+ — missing manifest.json error
sidebar_position: 100
description: How to resolve DagsterDbtManifestNotFoundError when deploying DbtProjectComponent, plus guidance on selectors, cross-code-location dependencies, and column lineage.
---

## Problem description

Users frequently ask whether the `DbtProjectComponent` supports filtering dbt projects using dbt selectors, as the documentation primarily shows examples using `select` and `exclude` parameters.

## Root cause

**As of Dagster 1.12.0:** The `DbtProjectComponent` does **not** directly support dbt selectors through a selector parameter.

## Solution

While DbtProjectComponent does not directly support selectors, there are several effective workarounds available.

#### 1. Use `@dbt_assets` with selectors (recommended)

The `@dbt_assets` decorator fully supports dbt selectors:

```python
from dagster_dbt import dbt_assets, DbtCliResource
from dagster import AssetExecutionContext

@dbt_assets(
    manifest=dbt_manifest_path,
    selector="my_selector_name"  # Supported
)
def my_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
    yield from dbt.cli(["build"], context=context).stream()
```

#### 2. Use select/exclude with tag-based selection

In your `DbtProjectComponent`, use tags to achieve selector-like behavior:

```yaml
# defs.yaml
type: dagster_dbt.DbtProjectComponent
attributes:
  project:
    project_dir: '{{ project_root }}/path/to/dbt_project'
  select: 'tag:my_tag' # Works like a selector
  exclude: 'tag:exclude_tag'
```

#### 3. Create dbt selectors and reference by tag

In your dbt project, create `selectors.yml`:

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

Then use the tag in your component:

```yaml
type: dagster_dbt.DbtProjectComponent
attributes:
  project:
    project_dir: '{{ project_root }}/dbt_project'
  select: 'tag:business_core' # References your selector logic
```

#### 4. Path-based selection

Use path selection, which mimics selector functionality:

```yaml
type: dagster_dbt.DbtProjectComponent
attributes:
  project:
    project_dir: '{{ project_root }}/dbt_project'
  select: 'path:models/marts/' # Select specific paths
  exclude: 'path:models/staging/' # Exclude others
```

## Upstream dependencies with DbtProjectComponent

### Setting up cross-code-location dependencies

You can establish dependencies between non-dbt assets and `DbtProjectComponent` assets across different code locations:

**Step 1:** Define your ingestion asset:

```python
# In your ingestion code location
@asset(key_prefix=["my_ingestion"])
def my_table():
    # API ingestion logic
    return data
```

**Step 2:** Create dbt source configuration:

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

**Step 3:** Reference in dbt models:

```sql
-- models/my_model.sql
select * from {{ source('my_ingestion', 'my_table') }}
```

**Result:** Dagster automatically establishes dependencies across code locations based on matching asset keys.

## Deployment considerations

### Missing manifest error

When deploying `DbtProjectComponent` to Dagster+, you may encounter:

```text
DagsterDbtManifestNotFoundError: /path/to/target/manifest.json does not exist.
```

**Solution:** Add dbt parsing to your CI/CD:

```yaml
# GitHub Actions example
- name: Prepare dbt projects
  run: |
    cd path/to/dbt/project
    dbt deps
    dbt parse

- name: Deploy to Dagster+
  run: |
    dagster-cloud ci deploy --location-name=$DAGSTER_CODE_LOCATION_NAME
```

**For Docker deployments**, add to your Dockerfile:

```dockerfile
# Install dbt dependencies and generate manifest
RUN cd /path/to/dbt/project && \
    dbt deps && \
    dbt parse
```

### Column lineage with `DbtProjectComponent`

**Configuration:**

```yaml
type: dagster_dbt.DbtProjectComponent
attributes:
  project:
    project_dir: '{{ project_root }}/dbt_project'
  include_metadata:
    - column_metadata # Available in Dagster 1.11.13+
```

:::note

Column lineage appears **after** materializing the dbt assets, not immediately upon loading the definitions.

:::

## When to use each approach

| Use Case                    | Recommendation                    | Reason                              |
| --------------------------- | --------------------------------- | ----------------------------------- |
| Need dbt selectors          | `@dbt_assets`                     | Full selector support               |
| Simple tag/path filtering   | `DbtProjectComponent`             | Easier configuration                |
| Cross-location dependencies | Either (with proper source setup) | Works with both approaches          |
| Large projects              | `DbtProjectComponent`             | Better performance, modern approach |
| Complex customization       | `@dbt_assets`                     | More flexibility                    |

## Future roadmap

The Dagster team is working to ensure that components support all features currently available in the `@dbt_assets` decorator, including native selector support.

For now, the tag-based and path-based selection approaches provide equivalent functionality to dbt selectors when used with `DbtProjectComponent`.
