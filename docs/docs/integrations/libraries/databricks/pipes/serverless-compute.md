---
title: Dagster Pipes with Databricks (serverless compute)
sidebar_position: 10
description: Use Dagster Pipes to orchestrate serverless Databricks notebooks with real-time log streaming and structured metadata reporting.
---

[Dagster Pipes](/integrations/external-pipelines) lets you run code in Databricks while streaming logs and structured metadata back to Dagster in real time. Unlike [Databricks Connect](/integrations/libraries/databricks/databricks-connect), the computation runs entirely on Databricks — your Dagster asset acts as the orchestrator, not the executor.

:::note
To use Dagster Pipes to deploy Python scripts to DBFS on classic (non-serverless) clusters, see [Dagster Pipes with Databricks (DBFS, classic clusters)](/integrations/libraries/databricks/pipes/classic-clusters).
:::

## When to use Dagster Pipes

Dagster Pipes is best for:

- Existing Databricks notebooks or scripts you want to orchestrate without rewriting
- Large batch jobs that should execute independently of the Dagster process
- Scenarios where you need real-time log streaming and structured metadata back in Dagster
- Teams where Databricks jobs are deployed and managed separately from Dagster code

## Prerequisites

Install the `dagster-databricks` library:

<Tabs>
  <TabItem value="uv" label="uv">

```shell
uv add dagster-databricks
```

  </TabItem>
  <TabItem value="pip" label="pip">

```shell
pip install dagster-databricks
```

  </TabItem>
</Tabs>

Configure your environment:

```bash
export DATABRICKS_HOST=https://dbc-xxxxxxx-yyyy.cloud.databricks.com/
export DATABRICKS_TOKEN=<your-personal-access-token>
```

For serverless compute, DBFS is unavailable. Use `PipesDatabricksServerlessClient`, which uses a Unity Catalog Volume as the message transport layer.

## Step 1: Configure the Pipes resource

<CodeExample
  path="docs_snippets/docs_snippets/integrations/databricks/databricks_pipes_uc_volumes.py"
  title="src/<project-name>/defs/databricks-assets.py"
/>

The `volume_path` must point to an existing Unity Catalog Volume (for example, `/Volumes/catalog/schema/dagster_pipes`). The client handles context injection and message reading automatically.

## Step 2: Add Pipes boilerplate to your notebook

On the Databricks side, wrap your notebook logic with `open_dagster_pipes` using the Unity Catalog loaders:

<CodeExample
  path="docs_snippets/docs_snippets/integrations/databricks/databricks_notebook_uc_volumes.py"
  title="Databricks notebook"
/>

The `PipesDatabricksNotebookWidgetsParamsLoader` reads Pipes parameters from notebook widget values, which `PipesDatabricksServerlessClient` injects automatically when it submits the run.

## Triggering existing jobs without Pipes

If your existing Databricks notebook or job doesn't have Pipes boilerplate, you can still orchestrate it from Dagster using the Databricks SDK directly. This approach blocks downstream assets on job failure and surfaces run metadata, but doesn't support real-time log streaming.

<CodeExample
  path="docs_snippets/docs_snippets/integrations/databricks/databricks_run_now.py"
  title="src/<project-name>/defs/databricks-assets.py"
/>

`client.jobs.run_now(job_id=...).result()` blocks until the job completes and raises an exception on failure, which surfaces as an asset failure in the Dagster UI.

## Advanced usage

For advanced scenarios such as streaming materializations mid-run, custom context loaders, or existing job-polling logic, see the [Dagster Pipes details and customization guide](/integrations/external-pipelines/dagster-pipes-details-and-customization).
