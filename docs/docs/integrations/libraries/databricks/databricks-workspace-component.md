---
title: Databricks Workspace Component
sidebar_position: 40
description: The Databricks Workspace Component is a state-backed component, which fetches and caches Databricks workspace metadata.
---

:::note Preview

`DatabricksWorkspaceComponent` is currently in **preview**. The API may change in future releases.

:::

:::info

`DatabricksWorkspaceComponent` is a [state-backed component](/guides/build/components/state-backed-components), which fetches and caches Databricks workspace metadata. For information on managing component state, see [Configuring state-backed components](/guides/build/components/state-backed-components/configuring-state-backed-components).

:::

The <PyObject section="libraries" module="dagster_databricks" integration="databricks" object="DatabricksWorkspaceComponent" /> connects directly to your Databricks workspace, discovers existing jobs, and exposes them as Dagster assets. Unlike the Asset Bundle component, it doesn't require a local `databricks.yml` file — it fetches job definitions from the workspace API at build time.

This approach is well suited for:

- Teams with existing Databricks jobs that want to orchestrate them through Dagster without restructuring
- Workspaces with many jobs where manual asset definition would be impractical
- Scenarios where jobs are managed directly in the Databricks workspace UI

## How it works

1. The component connects to your Databricks workspace using the provided credentials
2. It fetches job definitions (filtered by your configuration) and caches them as state
3. Each job's tasks are represented as Dagster assets with dependency information preserved
4. When materialized, the component triggers a job run via the Databricks API and monitors it to completion

## Step 1: Prepare a Dagster project

To begin, you'll need a Dagster project. You can use an [existing components-ready project](/guides/build/projects/moving-to-components/migrating-project) or create a new one:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/databricks-components/databricks-workspace-component/1-scaffold-project.txt" />

Activate the project virtual environment:

```
source ../.venv/bin/activate
```

Finally, add the `dagster-databricks` library to the project:

<PackageInstallInstructions packageName="dagster-databricks" />

## Step 2: Scaffold the component definition

Now that you have a Dagster project, you can scaffold a `DatabricksWorkspaceComponent` component definition. You'll need to provide:

- The URL of your Databricks workspace host
- The name of the environment variable that stores your Databricks workspace token

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/databricks-components/databricks-workspace-component/2-scaffold-defs.txt" />

The `dg scaffold defs` call will generate a `defs.yaml` file:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/databricks-components/databricks-workspace-component/3-tree.txt" />

The `defs.yaml` defines the component in your project:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/databricks-components/databricks-workspace-component/defs.yml" />

## Step 3: Customize component configuration

### Job filtering

You can filter which Databricks jobs to include using the `databricks_filter` key:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/databricks-components/databricks-workspace-component/defs-job-filter.yml" />

### Custom asset mapping

Similar to the Asset Bundle component, you can provide a custom mapping from task keys to asset specs:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/databricks-components/databricks-workspace-component/defs-custom-mapping.yml" />

## Best practices

### Workspace organization

Organize your Databricks workspace files in a structured hierarchy that reflects your data pipeline layers, and use descriptive file names that clearly indicate the transformation being performed (for example, `extract_customers.py` instead of `script_1.py`):

```txt
/Workspace/dagster_assets/
  ├── raw/              # Bronze layer
  │   ├── extract_customers.py
  │   └── extract_orders.py
  ├── staging/          # Silver layer
  │   ├── clean_customers.py
  │   └── clean_orders.py
  └── marts/            # Gold layer
      └── customer_analytics.py
```

### Signaling completion

Ensure your Databricks scripts signal completion status:

```python
# At the end of your notebook/script
def main():
    # Your processing logic
    result = process_data()

    # Save output to Delta Lake
    result.write.format("delta").mode("overwrite").save("/mnt/data/customers")

    # Signal successful completion
    dbutils.notebook.exit("success")

if __name__ == "__main__":
    main()
```

### Managing dependencies

Dependencies can be detected automatically by the component through Delta table paths:

```python
# Upstream asset: extract_customers.py
df.write.format("delta").save("/mnt/data/raw/customers")

# Downstream asset: clean_customers.py
# Component auto-detects dependency from read operation
df = spark.read.format("delta").load("/mnt/data/raw/customers")
```

For more complex dependency scenarios, use explicit configuration:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/databricks-components/databricks-workspace-component/defs-dependencies.yml" />
