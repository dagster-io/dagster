---
title: dbt patterns and best practices
description: Best practices and advanced patterns for dbt.
sidebar_position: 50
---

This guide covers advanced patterns and best practices for integrating dbt with Dagster, helping you build more maintainable data pipelines.

## Preventing concurrent dbt snapshots

[dbt snapshots](https://docs.getdbt.com/docs/build/snapshots) track changes to data over time by comparing current data to previous snapshots. Running snapshots concurrently can corrupt these tables, so it's critical to ensure only one snapshot operation runs at a time.

### 1. Separate snapshots from other models

Create separate dbt component definitions to isolate snapshots from your regular dbt models. First, scaffold two dbt components:

```bash
# Create component for regular models
dg scaffold defs dagster_dbt.DbtProjectComponent dbt_models

# Create component for snapshots
dg scaffold defs dagster_dbt.DbtProjectComponent dbt_snapshots
```

Configure the regular models component to exclude snapshots:

<CodeExample
  path="docs_snippets/docs_snippets/integrations/dbt/component/snapshot/models.yaml"
  title="my_project/defs/dbt_models/defs.yaml"
  language="yaml"
/>

Configure the snapshots component with concurrency control:

<CodeExample
  path="docs_snippets/docs_snippets/integrations/dbt/component/snapshot/snapshot.yaml"
  title="my_project/defs/dbt_snapshots/defs.yaml"
  language="yaml"
/>

### 2. Configure concurrency pools

Configure your Dagster instance to create pools with maximum concurrency of 1. Add this configuration to your `dagster.yaml` (for Dagster Open Source) or deployment settings (for Dagster+):

<CodeExample
  path="docs_snippets/docs_snippets/integrations/dbt/component/snapshot/dagster.yaml"
  title="dagster.yaml"
  language="yaml"
/>

Then set the pool limit for the snapshot pool:

```bash
# Set pool limit using CLI
dagster instance concurrency set dbt-snapshots 1
```

### 3. Manage multiple snapshot groups with Dagster components

For large projects with many snapshots, you can create multiple snapshot groups while still preventing concurrency issues within each group. Create separate [Dagster components](/guides/build/components/creating-new-components/creating-and-registering-a-component) for different business domains:

```bash
# Create component for sales snapshots
dg scaffold defs dagster_dbt.DbtProjectComponent dbt_snapshots_sales

# Create component for inventory snapshots
dg scaffold defs dagster_dbt.DbtProjectComponent dbt_snapshots_inventory
```

Sales snapshots component:

<CodeExample
  path="docs_snippets/docs_snippets/integrations/dbt/component/snapshot/snapshot_sales.yaml"
  title="my_project/defs/dbt_snapshots_sales/defs.yaml"
  language="yaml"
/>

Inventory snapshots component:

<CodeExample
  path="docs_snippets/docs_snippets/integrations/dbt/component/snapshot/snapshot_inventory.yaml"
  title="my_project/defs/dbt_snapshots_inventory/defs.yaml"
  language="yaml"
/>

Configure separate [pool limits for each domain](/guides/operate/managing-concurrency/concurrency-pools#limit-the-number-of-assets-or-ops-actively-executing-across-all-runs). This approach allows snapshots from different business domains to run in parallel while preventing concurrent execution within each domain, reducing the risk of corruption while maintaining reasonable performance.
