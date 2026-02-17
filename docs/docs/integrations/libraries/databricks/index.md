---
title: Dagster & Databricks
sidebar_label: Databricks
sidebar_position: 1
description: The dagster-databricks library provides multiple ways to orchestrate Databricks from Dagster, including Dagster Pipes for launching individual jobs, the DatabricksAssetBundleComponent for Asset Bundle-based workflows, and the DatabricksWorkspaceComponent for automatically discovering and orchestrating jobs across your Databricks workspace.
tags: [dagster-supported, compute, component]
source: https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-databricks
pypi: https://pypi.org/project/dagster-databricks/
sidebar_custom_props:
  logo: images/integrations/databricks.svg
partnerlink: https://databricks.com/
canonicalUrl: '/integrations/libraries/databricks'
slug: '/integrations/libraries/databricks'
---

<p>{frontMatter.description}</p>

## Installation

<PackageInstallInstructions packageName="dagster-databricks" />

## Choosing an integration approach

The `dagster-databricks` library offers five approaches for integrating Databricks with Dagster:

| Approach | Best for | How it works |
|----------|----------|--------------|
| **[Databricks Connect](#databricks-connect)** | Centralized Python code with remote Spark execution | Write Spark code in Dagster assets that executes on Databricks compute |
| **[Dagster Pipes](#dagster-pipes)** | Full control over individual job submissions with real-time monitoring | Submit Databricks jobs and stream logs/metadata back to Dagster |
| **[DatabricksAssetBundleComponent](#databricks-asset-bundle-component)** | Teams using [Databricks Asset Bundles](https://docs.databricks.com/en/dev-tools/bundles/index.html) | Reads your `databricks.yml` bundle config and creates Dagster assets from job tasks |
| **[DatabricksWorkspaceComponent](#databricks-workspace-component)** | Discovering and orchestrating existing workspace jobs | Connects to your workspace, discovers jobs, and exposes them as Dagster assets |
| **[Databricks Connections](#databricks-connections-dagster-cloud)** | Metadata discovery and lineage tracking (Dagster Cloud only) | Uses Datahub to automatically discover Databricks tables and catalogs as external assets |

## Databricks Connect

Databricks Connect allows you to centralize your Python code in your Dagster project while executing Spark workloads remotely on a Databricks cluster. Unlike job submission approaches, your code runs in the Dagster process but Spark operations execute on Databricks compute.

### When to use Databricks Connect

Databricks Connect is ideal for:
- Interactive development and quick iterations
- Centralized code that doesn't need deployment to Databricks
- Moderate-sized workloads where you want simpler debugging
- Greenfield Databricks use cases

It's not suitable for:
- Large batch jobs that should run independently
- Long-running workloads that would block the Dagster process
- Scenarios where network connectivity to Databricks is unreliable

### Setup

First, install the `databricks-connect` package and configure your environment:

```bash
pip install databricks-connect
export DATABRICKS_HOST=https://dbc-xxxxxxx-yyyy.cloud.databricks.com/
export DATABRICKS_TOKEN=<your-personal-access-token>
```

### Example

```python
import dagster as dg
from databricks.connect import DatabricksSession
from pyspark.sql import SparkSession
import os

# Create the Databricks session resource
databricks_session = (
    DatabricksSession.builder.remote(
        host=os.environ["DATABRICKS_HOST"],
        token=os.environ["DATABRICKS_TOKEN"],
    )
    .serverless()
    .getOrCreate()
)

@dg.asset
def my_spark_asset(
    context: dg.AssetExecutionContext,
    spark: dg.ResourceParam[SparkSession]
):
    # This code runs in Dagster, but Spark operations execute on Databricks
    df = spark.sql("SELECT * FROM catalog.schema.table")
    result = df.filter(df.status == "active").count()
    return dg.MaterializeResult(metadata={"row_count": result})

defs = dg.Definitions(
    assets=[my_spark_asset],
    resources={"spark": databricks_session},
)
```

In this example:
- The Python code runs in your Dagster deployment
- Spark DataFrame operations execute remotely on Databricks
- You have direct access to the Spark API within your asset functions
- No job submission overhead for interactive workloads

## Dagster Pipes

The `PipesDatabricksClient` resource enables you to launch Databricks jobs directly from Dagster assets and ops. This allows you to pass parameters to Databricks code while Dagster receives real-time events, such as logs, asset checks, and asset materializations from the initiated jobs.

### All-purpose compute example

<CodeExample path="docs_snippets/docs_snippets/integrations/databricks/dagster_code.py" language="python" />

<CodeExample path="docs_snippets/docs_snippets/integrations/databricks/databricks_code.py" language="python" />

### Serverless compute example

Using Pipes with Databricks serverless compute is slightly different. First, you can't specify library dependencies, you must instead define dagster-pipes as a dependency in the notebook environment.

Second, you must use Volumes for context loading and message writing, since DBFS is incompatible with serverless compute.

<CodeExample path="docs_snippets/docs_snippets/integrations/databricks/dagster_code_serverless.py" language="python" />

<CodeExample
  path="docs_snippets/docs_snippets/integrations/databricks/databricks_code_serverless.py"
  language="python"
/>

## Databricks Asset Bundle component

:::note Preview

`DatabricksAssetBundleComponent` is currently in **preview**. The API may change in future releases.

:::

The `DatabricksAssetBundleComponent` integrates with [Databricks Asset Bundles](https://docs.databricks.com/en/dev-tools/bundles/index.html), which provide a way to define Databricks jobs, pipelines, and configuration as code using YAML. The component reads your `databricks.yml` bundle config and automatically creates Dagster assets from the job tasks defined within it.

This approach is well suited for teams that are already using Databricks Asset Bundles to manage their Databricks workflows and want to bring them into Dagster without rewriting job definitions.

### How it works

1. You define your Databricks jobs and tasks in a standard `databricks.yml` bundle configuration
2. The component parses the bundle config and discovers all job tasks (notebook, Python wheel, Spark Python, Spark JAR, etc.)
3. Each task is represented as a Dagster asset with dependency information preserved
4. When materialized, the component submits the task to Databricks and monitors execution

### Scaffold the component

```bash
dg scaffold dagster_databricks.DatabricksAssetBundleComponent my_databricks_bundle \
  --databricks-config-path /path/to/databricks.yml \
  --databricks-workspace-host https://your-workspace.cloud.databricks.com \
  --databricks-workspace-token $DATABRICKS_TOKEN
```

### Configuration

The scaffolded `defs.yaml` defines the component:

```yaml
# my_project/defs/my_databricks_bundle/defs.yaml
type: dagster_databricks.DatabricksAssetBundleComponent
attributes:
  databricks_config_path: "{{ project_root }}/path/to/databricks.yml"
  workspace:
    host: https://your-workspace.cloud.databricks.com
    token: ${DATABRICKS_TOKEN}
```

#### Compute configuration

You can specify how tasks should be executed on Databricks using one of three compute options:

<Tabs>
<TabItem value="serverless" label="Serverless (default)">

```yaml
type: dagster_databricks.DatabricksAssetBundleComponent
attributes:
  databricks_config_path: "{{ project_root }}/path/to/databricks.yml"
  workspace:
    host: https://your-workspace.cloud.databricks.com
    token: ${DATABRICKS_TOKEN}
  compute_config:
    is_serverless: true
```

</TabItem>
<TabItem value="new_cluster" label="New cluster">

```yaml
type: dagster_databricks.DatabricksAssetBundleComponent
attributes:
  databricks_config_path: "{{ project_root }}/path/to/databricks.yml"
  workspace:
    host: https://your-workspace.cloud.databricks.com
    token: ${DATABRICKS_TOKEN}
  compute_config:
    spark_version: "13.3.x-scala2.12"
    node_type_id: "i3.xlarge"
    num_workers: 2
```

</TabItem>
<TabItem value="existing_cluster" label="Existing cluster">

```yaml
type: dagster_databricks.DatabricksAssetBundleComponent
attributes:
  databricks_config_path: "{{ project_root }}/path/to/databricks.yml"
  workspace:
    host: https://your-workspace.cloud.databricks.com
    token: ${DATABRICKS_TOKEN}
  compute_config:
    existing_cluster_id: "1234-567890-abcde123"
```

</TabItem>
</Tabs>

#### Custom asset mapping

By default, the component creates one Dagster asset per Databricks task. You can override this by providing a custom mapping from task keys to asset specs:

```yaml
type: dagster_databricks.DatabricksAssetBundleComponent
attributes:
  databricks_config_path: "{{ project_root }}/path/to/databricks.yml"
  workspace:
    host: https://your-workspace.cloud.databricks.com
    token: ${DATABRICKS_TOKEN}
  assets_by_task_key:
    my_etl_task:
      - key: raw/customers
        description: "Raw customer data extracted from source"
      - key: raw/orders
        description: "Raw order data extracted from source"
```

### Supported task types

The component supports the following Databricks task types:

- **Notebook tasks** - Databricks notebooks
- **Spark Python tasks** - Python scripts run on Spark
- **Python wheel tasks** - Python wheel packages
- **Spark JAR tasks** - Java/Scala JARs run on Spark
- **Run job tasks** - References to other Databricks jobs
- **Condition tasks** - Conditional logic in workflows

## Databricks Workspace component

:::note Preview

`DatabricksWorkspaceComponent` is currently in **preview**. The API may change in future releases.

:::

:::info

`DatabricksWorkspaceComponent` is a [state-backed component](/guides/build/components/state-backed-components), which fetches and caches Databricks workspace metadata. For information on managing component state, see [Configuring state-backed components](/guides/build/components/state-backed-components/configuring-state-backed-components).

:::

The `DatabricksWorkspaceComponent` connects directly to your Databricks workspace, discovers existing jobs, and exposes them as Dagster assets. Unlike the Asset Bundle component, it doesn't require a local `databricks.yml` file — it fetches job definitions from the workspace API at build time.

This approach is well suited for:

- Teams with existing Databricks jobs that want to orchestrate them through Dagster without restructuring
- Workspaces with many jobs where manual asset definition would be impractical
- Scenarios where jobs are managed directly in the Databricks workspace UI

### How it works

1. The component connects to your Databricks workspace using the provided credentials
2. It fetches job definitions (filtered by your configuration) and caches them as state
3. Each job's tasks are represented as Dagster assets with dependency information preserved
4. When materialized, the component triggers a job run via the Databricks API and monitors it to completion

### Configuration

```yaml
# my_project/defs/my_databricks_workspace/defs.yaml
type: dagster_databricks.DatabricksWorkspaceComponent
attributes:
  workspace:
    host: https://your-workspace.cloud.databricks.com
    token: ${DATABRICKS_TOKEN}
```

#### Filtering jobs

You can filter which Databricks jobs to include using the `databricks_filter` key:

```yaml
type: dagster_databricks.DatabricksWorkspaceComponent
attributes:
  workspace:
    host: https://your-workspace.cloud.databricks.com
    token: ${DATABRICKS_TOKEN}
  databricks_filter:
    include_jobs:
      job_ids:
        - 12345
        - 67890
```

#### Custom asset mapping

Similar to the Asset Bundle component, you can provide a custom mapping from task keys to asset specs:

```yaml
type: dagster_databricks.DatabricksWorkspaceComponent
attributes:
  workspace:
    host: https://your-workspace.cloud.databricks.com
    token: ${DATABRICKS_TOKEN}
  assets_by_task_key:
    etl_extract:
      - key: raw/customers
        description: "Customers extracted from source database"
    etl_transform:
      - key: staging/customers_clean
        description: "Cleaned and validated customer data"
```

### Best practices

#### Workspace organization

Organize your Databricks workspace files in a structured hierarchy that reflects your data pipeline layers:

```
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

Use descriptive file names that clearly indicate the transformation being performed (e.g., `extract_customers.py` instead of `script_1.py`).

#### Signaling completion

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

#### Managing dependencies

Dependencies can be detected automatically by the component through Delta table paths:

```python
# Upstream asset: extract_customers.py
df.write.format("delta").save("/mnt/data/raw/customers")

# Downstream asset: clean_customers.py
# Component auto-detects dependency from read operation
df = spark.read.format("delta").load("/mnt/data/raw/customers")
```

For more complex dependency scenarios, use explicit configuration:

```yaml
type: dagster_databricks.DatabricksWorkspaceComponent
attributes:
  workspace:
    host: https://your-workspace.cloud.databricks.com
    token: ${DATABRICKS_TOKEN}
  asset_overrides:
    customer_analytics:
      depends_on:
        - clean_customers
        - clean_orders
```

## Decision guide

### Choose Databricks Connect when:
- You want to write Spark code directly in your Dagster assets
- You prefer centralized code that doesn't need deployment to Databricks
- You're doing interactive development or quick iterations
- Your workloads are moderate in size and duration
- You want simpler debugging with local code execution

### Choose Dagster Pipes when:
- You need real-time log streaming from Databricks to Dagster
- Databricks job code needs to report custom metadata back to Dagster
- You're running large batch jobs that should execute independently
- You want fine-grained control over job submission parameters
- Your code is already deployed to Databricks

### Choose DatabricksAssetBundleComponent when:
- You want Databricks job definitions version-controlled with your Dagster code
- You're starting fresh or migrating jobs to a new structure
- You need tight integration between job config and Dagster definitions
- CI/CD pipelines manage your Databricks deployments

### Choose DatabricksWorkspaceComponent when:
- Jobs already exist in Databricks and are managed there
- You want Dagster to discover and orchestrate existing jobs
- Teams manage jobs directly in Databricks UI/API
- You need flexibility without maintaining local config files

### Choose Databricks Connections when:
- You're on Dagster Cloud
- You want visibility into Databricks tables/catalogs as external assets
- Data governance and lineage tracking are priorities
- You don't need to orchestrate jobs, just observe metadata
- You want automatic schema and statistics extraction

## Databricks Connections (Dagster Cloud)

:::note Dagster Cloud only

This feature is only available in Dagster Cloud. It is not available in open-source Dagster.

:::

Databricks Connections is a Dagster Cloud feature that uses Datahub to automatically discover and ingest metadata from Databricks tables, catalogs, and schemas as external assets. This provides visibility into your Databricks environment without requiring job orchestration.

### When to use Databricks Connections

Use Databricks Connections when you want to:
- Gain visibility into Databricks tables and catalogs as external assets
- Track data lineage from Databricks in Dagster
- Extract metadata like schemas, row counts, and table statistics
- Implement data governance and cataloging
- Observe data without orchestrating job execution

Note that this approach is **read-only** - you cannot materialize or orchestrate jobs through Connections. For job orchestration, use one of the other integration approaches.

### Configuration

Databricks Connections are configured through the Dagster Cloud UI:

1. Navigate to your Dagster Cloud deployment settings
2. Add a new Databricks connection
3. Provide:
   - Workspace URL
   - Personal Access Token (stored as an environment variable)
   - Filter patterns for catalogs, schemas, tables, notebooks, and views

### How it works

1. A scheduled sync (configured with a cron expression) connects to Databricks via the Datahub connector
2. Discovers tables and extracts metadata including schemas, row counts, and sizes
3. Converts discovered resources to Dagster external assets
4. Reports observations to Dagster for lineage tracking

The sync runs in the background and keeps your asset metadata current without requiring code changes.

### Comparison with other approaches

| Feature | Connections | Components/Pipes |
|---------|-------------|------------------|
| **Job orchestration** | No | Yes |
| **Metadata extraction** | Rich (schemas, stats, lineage) | Basic |
| **Setup** | UI configuration only | Code required |
| **Discovery** | Automatic | Manual or component-based |
| **Use case** | Observability & governance | Orchestration & execution |

## About Databricks

**Databricks** is a unified data analytics platform that simplifies and accelerates the process of building big data and AI solutions. It integrates seamlessly with Apache Spark and offers support for various data sources and formats. Databricks provides powerful tools to create, run, and manage data pipelines, making it easier to handle complex data engineering tasks. Its collaborative and scalable environment is ideal for data engineers, scientists, and analysts who need to process and analyze large datasets efficiently.
