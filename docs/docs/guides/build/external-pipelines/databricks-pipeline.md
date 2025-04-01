---
title: Build pipelines with Databricks
description: "Learn to integrate Dagster Pipes with Databricks to launch external code from Dagster assets."
sidebar_position: 50
---

This article covers how to use [Dagster Pipes](/guides/build/external-pipelines/) with Dagster's [Databricks integration](/integrations/libraries/databricks) to launch Databricks jobs.

Pipes allows your Databricks jobs to stream logs (including `stdout` and `stderr` of the driver process) and events back to Dagster. This does not require a full Dagster environment on Databricks; instead:

- The Databricks environment needs to include [`dagster-pipes`](https://pypi.org/project/dagster-pipes), a single-file Python package with no dependencies that can be installed from PyPI or easily vendored, and
-  Databricks jobs must be launched from Dagster

<details>
    <summary>Prerequisites</summary>

    - **In the Dagster environment**, you'll need to install the following packages:

    ```shell
    pip install dagster dagster-webserver dagster-databricks
    ```

    Refer to the [Dagster installation guide](/getting-started/installation) for more info.

    - **In Databricks**, you'll need:

    - **A Databricks workspace**. If you don't have this, follow the [Databricks quickstart](https://docs.databricks.com/workflows/jobs/jobs-quickstart.html) to set one up.
    - **The following information about your Databricks workspace**:

        - `host` - The host URL of your Databricks workspace, ex: `https://dbc-xxxxxxx-yyyy.cloud.databricks.com/`
        - `token` - A personal access token for the Databricks workspace. Refer to the Databricks API authentication documentation for more info about retrieving these values.

        You should set and export the Databricks host and token environment variables in your shell session:

        ```shell
        export DATABRICKS_HOST=<your-host-url>
        export DATABRICKS_TOKEN<your-personal-access-token>
        ```

</details>

## Step 1: Create an asset computed in Databricks

In this step, you'll create a Dagster asset that, when materialized, opens a Dagster pipes session and launches a Databricks job.

### Step 1.1: Define the Dagster asset

In your Dagster project, create a file named `dagster_databricks_pipes.py` and paste in the following code:

<CodeExample path="docs_snippets/docs_snippets/guides/dagster/dagster_pipes/databricks/databricks_asset_client.py" startAfter="start_databricks_asset" endBefore="end_databricks_asset" />

Let's review what's happening in this code:

- **Includes a number of imports from Dagster and the Databricks SDK.** There are a few that aren't used in this code block, but will be later in this guide.

- **Creates an asset named `databricks_asset`.** We also:

  - Provided <PyObject section="execution" module="dagster" object="AssetExecutionContext" /> as the `context` argument to the asset. This object provides access to system APIs such as resources, config, and logging. We'll come back to this a bit later in this section.
  - Specified a <PyObject section="libraries" module="dagster_databricks" object="PipesDatabricksClient" /> resource for the asset to use. We'll also come back to this later.

- **Defines a Databricks `SubmitTask` object in the asset body.** Coverage of all the fields on this object is beyond the scope of this guide, but you can find further information in the [Databricks SDK API docs](https://databricks-sdk-py.readthedocs.io/en/latest/workspace/jobs/jobs.html) and [source code](https://github.com/databricks/databricks-sdk-py/blob/main/databricks/sdk/service/jobs.py) for the `SubmitTask` object.

  The submitted task must:

  - **Specify `dagster-pipes` as a PyPI dependency**. You can include a version pin (e.g. `dagster-pipes==1.5.4`) if desired.
  - Use a `spark_python_task`.
  - Specify either `new_cluster` (this is the **recommended approach**) or `existing_cluster_id`. The `new_cluster` field is used in this example.
    - If `new_cluster` is set, then setting `new_cluster.cluster_log_conf.dbfs` enables the <PyObject section="libraries" object="PipesDatabricksClient" module="dagster_databricks" /> to automatically set up <PyObject section="libraries" object="PipesDbfsLogReader" module="dagster_databricks" />  objects for `stdout` and `stderr` of the driver process. These will periodically forward the `stdout` and `stderr` logs written by Databricks back to Dagster. **Note**: Because Databricks only updates these log files every five minutes, that is the maximum frequency at which Dagster can forward the logs.
    - If `existing_cluster_id` is set, <PyObject section="libraries" object="PipesDatabricksClient" module="dagster_databricks" /> won't be able to forward `stdout` and `stderr` driver logs to Dagster. Using an existing cluster **requires passing an instance of <PyObject section="libraries" object="PipesCliArgsParamsLoader" module="dagster_pipes" /> to <PyObject section="libraries" object="open_dagster_pipes" module="dagster_pipes" />** in the Python script which is executed on Databricks. This is because setting environment variables is only possible when creating a new cluster, so we have to use the alternative method of passing Pipes parameters as command-line arguments.

- **Defines an `extras` dictionary containing some arbitrary data (`some_parameter`).** This is where you can put various data, e.g. from the Dagster run config, that you want to be available in Databricks. Anything added here must be JSON-serializable.

- **Passes the `SubmitTask` object, `AssetExecutionContext`, and `extras` dictionary to the `run` method of <PyObject section="libraries" module="dagster_databricks" object="PipesDatabricksClient" />**. This method synchronously executes the Databricks job specified by the `SubmitTask` object. It slightly modifies the object by injecting some environment variables under `new_cluster.spark_env_vars` before submitting the object to the Databricks API.

- **Returns a <PyObject section="assets" module="dagster" object="MaterializeResult" /> object representing the result of execution**. This is obtained by calling `get_materialize_result` on the `PipesClientCompletedInvocation` object returned by `run` after the Databricks job has finished. **Note**: Execution can take several minutes even for trivial scripts due to Databricks cluster provisioning times.
{/* TODO replace `PipesClientCompletedInvocation` with <PyObject section="pipes" module="dagster" object="PipesClientCompletedInvocation" /> */}

### Step 1.2: Define the Databricks Pipes client and definitions

The [`dagster-databricks`](/api/python-api/libraries/dagster-databricks) library provides a <PyObject section="libraries" module="dagster_databricks" object="PipesDatabricksClient" />, which is a pre-built Dagster resource that allows you to quickly get Pipes working with your Databricks workspace.

Add the following to the bottom of `dagster_databricks_pipes.py` to define the resource and a <PyObject section="definitions" module="dagster" object="Definitions" /> object that binds it to the `databricks_asset`:

<CodeExample path="docs_snippets/docs_snippets/guides/dagster/dagster_pipes/databricks/databricks_asset_client.py" startAfter="start_definitions" endBefore="end_definitions" />

## Step 2: Write a script for execution on Databricks

The next step is to write the code that will be executed on Databricks. In the Databricks task specification in [Step 1.1](#step-11-define-the-dagster-asset), we referenced a file `dbfs:/my_python_script.py` in the `spark_python_task`:

```python
"spark_python_task": {
   "python_file": "dbfs:/my_python_script.py",   # location of target code file
   "source": jobs.Source.WORKSPACE,
}
```

We'll create this script from scratch and upload it to DBFS. You can use the Databricks UI or run a command from a shell to do this. To use the shell method, run:

```shell
dbfs cp my_python_script.py dbfs:/my_python_script.py
```

Let's look at the script itself:

<CodeExample path="docs_snippets/docs_snippets/guides/dagster/dagster_pipes/databricks/databricks_script.py" />

:::tip

The metadata format shown above (`{"raw_value": value, "type": type}`) is part of Dagster Pipes' special syntax for specifying rich Dagster metadata. For a complete reference of all supported metadata types and their formats, see the [Dagster Pipes metadata reference](using-dagster-pipes/reference#passing-rich-metadata-to-dagster).

:::

Before we go any futher, let's review what this script does:

- **Imports `PipesDbfsContextLoader`, `PipesDbfsMessageWriter`, and `open_dagster_pipes` from `dagster_pipes`.** The <PyObject section="libraries" object="PipesDbfsContextLoader" module="dagster_pipes" /> and <PyObject section="libraries" object="PipesDbfsMessageWriter" module="dagster_pipes" /> are DBFS-specific implementations of the <PyObject section="libraries" module="dagster_pipes" object="PipesContextLoader" /> and <PyObject section="libraries" module="dagster_pipes" object="PipesMessageWriter" />. Refer to the [Dagster Pipes details and customization Guide](/guides/build/external-pipelines/dagster-pipes-details-and-customization) for protocol details.

  Both objects write temporary files on DBFS for communication between the orchestration and external process. The <PyObject section="libraries" object="PipesDbfsContextLoader" module="dagster_pipes" /> and <PyObject section="libraries" object="PipesDbfsMessageWriter" module="dagster_pipes" /> match a corresponding `PipesDbfsContextInjector` and `PipesDbfsMessageReader` on the orchestration end, which are instantiated inside the <PyObject section="libraries" object="PipesDatabricksClient" module="dagster_databricks" />.

- **Passes the context loader and message writer to the <PyObject section="libraries" object="open_dagster_pipes" module="dagster_pipes" /> context manager**, which yields an instance of <PyObject section="libraries" object="PipesContext" module="dagster_pipes" /> called `pipes`. **Note**: when using `existing_cluster_id`, you must also import `PipesCliArgsParamsLoader` and pass an instance of it to `open_dagster_pipes` as the `params_loader` parameter.

  Inside the body of the context manager are various calls against `pipes` to retrieve an extra, log, and report an asset materialization. All of these calls will use the DBFS temporary file-based communications channels established by <PyObject section="libraries" object="PipesDbfsContextLoader" module="dagster_pipes" /> and <PyObject section="libraries" object="PipesDbfsMessageWriter" module="dagster_pipes" />. To see the full range of what you can do with the <PyObject section="libraries" object="PipesContext" module="dagster_pipes" />, see the API docs or the general [Pipes guide](/guides/build/external-pipelines/).

At this point you can execute the rest of your Databricks code as normal, invoking various <PyObject section="libraries" object="PipesContext" module="dagster_pipes" /> APIs as needed.

#### Existing codebases

For illustrative purposes, we've created a Python script from scratch. However, you may want to apply Pipes to an existing codebase.

One approach that can be useful is to wrap the <PyObject section="libraries" object="open_dagster_pipes" module="dagster_pipes" /> context manager around an existing `main` function or entry point. You can either pass the <PyObject section="libraries" object="PipesContext" module="dagster_pipes" /> down through your business logic, or simply report an asset materialization after your business logic is done:

<CodeExample path="docs_snippets/docs_snippets/guides/dagster/dagster_pipes/databricks/databricks_script_existing.py" />

## Step 3: Run the Databricks job from the Dagster UI

In this step, you'll run the Databricks job you created in [Step 1.2](#step-12-define-the-databricks-pipes-client-and-definitions) from the Dagster UI.

1. In a new command line session, run the following to start the UI:

   ```shell
   dagster dev -f dagster_databricks_pipes.py
   ```

2. Navigate to [localhost:3000](http://localhost:3000/), where you should see the UI:

    ![Databricks asset](/images/guides/build/external-pipelines/databricks/asset.png)

3. Click **Materialize** near the top right corner of the page, then click **View** on the **Launched Run** popup. Wait for the run to complete, and the event log should look like this:

    ![Event log for Databricks run](/images/guides/build/external-pipelines/databricks/run.png)

## Advanced: Customization using open_pipes_session

The <PyObject section="libraries" object="PipesDatabricksClient" module="dagster_databricks" /> is a high-level API that doesn't cover all use cases. If you have existing code to launch/poll the job you do not want to change, you want to stream back materializations as they occur, or you just want more control than is permitted by <PyObject section="libraries" object="PipesDatabricksClient" module="dagster_databricks" />, you can use <PyObject section="pipes" module="dagster" object="open_pipes_session" /> instead of <PyObject section="libraries" object="PipesDatabricksClient" module="dagster_databricks" />.

To use <PyObject section="pipes" module="dagster" object="open_pipes_session" />:

1. Your Databricks job be launched within the scope of the `open_pipes_session` context manager; and
2. Your job is launched on a cluster containing the environment variables available on the yielded `pipes_session`

While your Databricks code is running, any calls to `report_asset_materialization` in the external script are streamed back to Dagster, causing a `MaterializeResult` object to be buffered on the `pipes_session`. You can either:

- Leave these objects buffered until execution is complete (**Option 1** in below example code), or
- Stream them to Dagster machinery during execution by calling `yield pipes_session.get_results()` (**Option 2**)

With either option, once the <PyObject section="pipes" module="dagster" object="open_pipes_session" /> block closes, you must call `yield pipes_session.get_results()` to yield any remaining buffered results, since we cannot guarantee that all communications from Databricks have been processed until the `open_pipes_session` block closes.

<CodeExample path="docs_snippets/docs_snippets/guides/dagster/dagster_pipes/databricks/databricks_asset_open_pipes_session.py" />
