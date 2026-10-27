---
title: Dagster Pipes with existing Databricks jobs
sidebar_label: Existing jobs (workflows)
sidebar_position: 30
description: Trigger an existing Databricks job with Dagster Pipes to stream logs and structured metadata back to Dagster.
---

import Preview from '@site/docs/partials/\_Preview.md';

<Preview />

If your work is already defined as a Databricks job (workflow), you can trigger it by ID with [Dagster Pipes](/integrations/external-pipelines) instead of rebuilding its tasks in Dagster. The job keeps its own tasks and compute; Dagster passes it a Pipes context and receives logs and metadata back.

Both Pipes clients support this with `run_job`:

| Client                            | Pipes storage        | Use with                                                           |
| --------------------------------- | -------------------- | ------------------------------------------------------------------ |
| `PipesDatabricksServerlessClient` | Unity Catalog Volume | Serverless jobs, and classic jobs on Unity Catalog-enabled compute |
| `PipesDatabricksClient`           | DBFS                 | Classic jobs in workspaces where DBFS is available                 |

To submit one-time runs from task definitions in Dagster instead, see [serverless compute](/integrations/libraries/databricks/pipes/serverless-compute) or [DBFS, classic clusters](/integrations/libraries/databricks/pipes/classic-clusters).

## Prerequisites

- The `dagster-databricks` library installed in your Dagster project, and the `DATABRICKS_HOST` and `DATABRICKS_TOKEN` environment variables set. See [serverless compute](/integrations/libraries/databricks/pipes/serverless-compute#prerequisites).
- [`dagster-pipes`](https://pypi.org/project/dagster-pipes) installed in the job's environment.
- An existing Databricks job, and its job ID.

## Step 1: Add the Pipes parameters to your job

Dagster passes the Pipes context to the job as two [job parameters](https://docs.databricks.com/aws/en/jobs/job-parameters): `DAGSTER_PIPES_CONTEXT` and `DAGSTER_PIPES_MESSAGES`. In the job's settings, declare both with an empty default value:

```json
"parameters": [
  {"name": "DAGSTER_PIPES_CONTEXT", "default": ""},
  {"name": "DAGSTER_PIPES_MESSAGES", "default": ""}
]
```

How a task receives these parameters depends on its type:

- **Notebook tasks** receive job parameters automatically as widgets. No further setup is needed.
- **Python script tasks** only receive what's listed in their task parameters. Forward both Pipes parameters as arguments:

  ```json
  "spark_python_task": {
    "python_file": "/Workspace/path/to/script.py",
    "parameters": [
      "--dagster-pipes-context", "{{job.parameters.DAGSTER_PIPES_CONTEXT}}",
      "--dagster-pipes-messages", "{{job.parameters.DAGSTER_PIPES_MESSAGES}}"
    ]
  }
  ```

:::note

All tasks in the run receive the same Pipes parameters, so only one task per run should report back to Dagster with Pipes.

:::

## Step 2: Add Pipes to the task code

Wrap the task's logic with `open_dagster_pipes`. The context loader and message writer must match your Dagster client: the Unity Catalog Volumes loaders for `PipesDatabricksServerlessClient`, or `PipesDbfsContextLoader` and `PipesDbfsMessageWriter` for `PipesDatabricksClient`.

<Tabs>
  <TabItem value="notebook" label="Notebook task">

Read the Pipes parameters from the notebook widgets with `PipesDatabricksNotebookWidgetsParamsLoader`:

<CodeExample
  path="docs_snippets/docs_snippets/integrations/databricks/databricks_notebook_uc_volumes.py"
  title="Databricks notebook"
/>

  </TabItem>
  <TabItem value="python-script" label="Python script task">

Read the Pipes parameters from the command-line arguments with `PipesCliArgsParamsLoader`:

<CodeExample
  path="docs_snippets/docs_snippets/integrations/databricks/databricks_script_run_job.py"
  title="Databricks Python script"
/>

  </TabItem>
</Tabs>

## Step 3: Trigger the job from Dagster

Call `run_job` with the job ID:

<CodeExample
  path="docs_snippets/docs_snippets/integrations/databricks/databricks_pipes_run_job.py"
  title="src/<project-name>/defs/databricks-assets.py"
/>

`run_job` waits for the job run to finish, and the asset fails if the run fails. If the Dagster run is canceled, the Databricks run is canceled too. Your own `job_parameters` are passed alongside the Pipes parameters, and `run_now_args` passes other options to `WorkspaceClient.jobs.run_now`, such as `only` to run a subset of tasks or `performance_target`.

## Triggering jobs without Pipes

If you can't add Pipes to the job's code, you can still trigger the job from Dagster and wait for it to finish, without streaming logs or metadata back. See [Triggering existing jobs without Pipes](/integrations/libraries/databricks/pipes/serverless-compute#triggering-existing-jobs-without-pipes), or use the [Databricks workspace component](/integrations/libraries/databricks/databricks-workspace-component) to model your jobs as assets.
