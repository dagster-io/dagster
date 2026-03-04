---
title: Spark Connect or Databricks Connect pipelines
description: 'Learn to integrate Spark Connect or Databricks Connect with Dagster to launch external compute from Dagster assets.'
sidebar_position: 51
---

import ScaffoldProject from '@site/docs/partials/\_ScaffoldProject.md';

This article covers how to use [Spark Connect](https://spark.apache.org/docs/latest/spark-connect-overview.html) or [Databricks Connect](https://docs.databricks.com/aws/en/dev-tools/databricks-connect/python) to run compute in Spark or Databricks from Dagster. These protocols allow you to centralize your Python code in your Dagster project and run it in Spark or Databricks.

## Prerequisites

<Tabs groupId="platform">
<TabItem value="Databricks Connect" label="Databricks Connect">
1.  Create a new Dagster project:
    <ScaffoldProject />
    Refer to the [Dagster installation guide](/getting-started/installation) for more info.
2.  Install the `databricks-connect` package, [based on your Python and Databricks Runtime version](https://docs.databricks.com/aws/en/dev-tools/databricks-connect/python/install#version-support-matrix):
    ```bash
    uv pip install databricks-connect
    ```
3.  In Databricks, you'll need:
    - **A Databricks workspace**. If you don't have this, follow the [Databricks quickstart](https://docs.databricks.com/workflows/jobs/jobs-quickstart.html) to set one up.
    - **The following information about your Databricks workspace**:

      - `host` - The host URL of your Databricks workspace, ex: `https://dbc-xxxxxxx-yyyy.cloud.databricks.com/`
      - `token` - A personal access token for the Databricks workspace. Refer to the Databricks API authentication documentation for more info about retrieving these values.

      You should set and export the Databricks host and token environment variables in your shell session:

      ```shell
      export DATABRICKS_HOST=<your-host-url>
      export DATABRICKS_TOKEN=<your-personal-access-token>
      ```

</TabItem>
<TabItem value="Spark Connect" label="Spark Connect">
1.  Create a new Dagster project:
    <ScaffoldProject />
    Refer to the [Dagster installation guide](/getting-started/installation) for more info.
2.  Install the `pyspark` package:
    ```bash
    uv pip install pyspark
    ```
3.  In Spark, you'll need:
    - **A running Spark Connect server**. If you don't have this, follow the [Spark Connect quickstart](https://spark.apache.org/docs/latest/spark-connect-overview.html#download-and-start-spark-server-with-spark-connect) to set one up.
    - **The following information about your Spark Connect server**:
      - `host` - The host URL of your Spark Connect server, by default `sc://localhost`.

      You should set and export the Spark Connect host environment variable in your shell session:

      ```shell
      export SPARK_REMOTE="sc://localhost"
      ```

</TabItem>
</Tabs>

## Step 1: Create an asset computed in Spark Connect or Databricks Connect

In this step, you'll create a set of Dagster assets that, when materialized, execute code in Spark Connect or Databricks Connect.

import ScaffoldAsset from '@site/docs/partials/\_ScaffoldAsset.md';

<ScaffoldAsset />

In your Dagster project, create a file named `spark_assets.py` and paste in the following code:

<CodeExample
  path="docs_snippets/docs_snippets/guides/tutorials/spark_connect/spark_assets.py"
  title="src/<project_name>/spark_assets.py"
/>

This code does the following:

- **Includes a number of imports from Dagster and pyspark.**

- **Creates two assets named `airport_temps` and `max_temps_by_code`.** The body of these assets are implemented as ordinary Spark connect scripts. We also:

  - Provided <PyObject section="execution" module="dagster" object="AssetExecutionContext" /> as the `context` argument to the asset. This object provides access to system APIs such as resources, config, and logging.
  - Specified a `SparkSession` resource for the asset to use. We will provide this resource in the next step, connecting to Spark Connect or Databricks Connect.

## Step 2: Define the Spark Connect or Databricks Connect resource and Definitions

import ScaffoldResource from '@site/docs/partials/\_ScaffoldResource.md';

<ScaffoldResource />

<Tabs groupId="platform">
<TabItem value="Databricks Connect" label="Databricks Connect">

Add the following to a new file named `databricks_resources.py` to define a `DatabricksSession` and a <PyObject section="definitions" module="dagster" object="Definitions" /> object that binds it to our assets as a resource:

<CodeExample
  path="docs_snippets/docs_snippets/guides/tutorials/spark_connect/databricks_resources.py"
  title="src/<project_name>/databricks_resources.py"
/>

</TabItem>
<TabItem value="Spark Connect" label="Spark Connect">

Add the following to a new file named `spark_resources.py` to define a `SparkSession` and a <PyObject section="definitions" module="dagster" object="Definitions" /> object that binds it to our assets as a resource:

<CodeExample
  path="docs_snippets/docs_snippets/guides/tutorials/spark_connect/spark_resources.py"
  title="src/<project_name>/spark_resources.py"
/>

</TabItem>
</Tabs>

## Step 3: Run the Spark Connect or Databricks Connect job from the Dagster UI

In this step, you'll run the Spark Connect or Databricks Connect job you created in [Step 1](#step-1-create-an-asset-computed-in-spark-connect-or-databricks-connect) from the Dagster UI.

1.  In a new command line session, run the following to start the UI:

    ```shell
    dg dev
    ```

2.  Navigate to [localhost:3000](http://localhost:3000), where you should see the UI:

    ![Spark assets](/images/tutorial/spark_connect/assets.png)

3.  Click **Materialize** near the top right corner of the page, then click **View** on the **Launched Run** popup. Wait for the run to complete, and the event log should look like this:

    ![Event log for Spark run](/images/tutorial/spark_connect/run.png)
