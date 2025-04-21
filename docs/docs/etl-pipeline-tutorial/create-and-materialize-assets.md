---
title: Create and materialize assets
description: Load project data and create and materialize assets
last_update:
  author: Alex Noonan
sidebar_position: 10
---

In the first step of the tutorial, you created your Dagster project with the raw data files. In this step, you will:

- Add a DuckDB resource
- Build software-defined assets
- Materialize your assets

## 1. Define the DuckDB resource

In Dagster, [Resources](/api/dagster/resources) are the external services, tools, and storage backends you need to do your job. For the storage backend in this project, we'll use [DuckDB](https://duckdb.org/), a fast, in-process SQL database that runs inside your application. We'll define it once, making it available to all assets and objects that need it.

We will create a file in the `defs` di

<CodeExample
  path="docs_snippets/docs_snippets/guides/tutorials/etl_tutorial/defs/resources.py"
  language="python"
/>

## 2. Create assets

Software defined <PyObject section="assets" module="dagster" object="asset" pluralize /> are the main building blocks in Dagster. An asset is composed of three components:

1. Asset key or unique identifier.
2. An op which is a function that is invoked to produce the asset.
3. Upstream dependencies that the asset depends on.

You can read more about our philosophy behind the [asset centric approach](https://dagster.io/blog/software-defined-assets).

### Products asset

First, we will create an asset that creates a DuckDB table to hold data from the products CSV. This asset takes the `duckdb` resource defined earlier and returns a <PyObject section="assets" module="dagster" object="MaterializeResult" /> object.
Additionally, this asset contains metadata in the <PyObject section="assets" module="dagster" object="asset" decorator /> decorator parameters to help categorize the asset, and in the `return` block to give us a preview of the asset in the Dagster UI.

To create this asset, we can use `dg` to generate the necessary file:

```bash
dg scaffold dagster.asset assets.py
```

Copy the following code into the `defs/assets.py` file:

<CodeExample
  path="docs_snippets/docs_snippets/guides/tutorials/etl_tutorial/defs/assets.py"
  language="python"
  startAfter="start_asset_products"
  endBefore="end_asset_products"
/>

### Sales reps asset

The code for the sales reps asset is similar to the product asset code. In the `definitions.py` file, copy the following code below the product asset code:

<CodeExample
  path="docs_snippets/docs_snippets/guides/tutorials/etl_tutorial/defs/assets.py"
  language="python"
  startAfter="start_asset_sales_reps"
  endBefore="end_asset_sales_reps"
/>

### Sales data asset

To add the sales data asset, copy the following code into your `definitions.py` file below the sales reps asset:

<CodeExample
  path="docs_snippets/docs_snippets/guides/tutorials/etl_tutorial/defs/assets.py"
  language="python"
  startAfter="start_asset_sales_data"
  endBefore="end_asset_sales_data"
/>

## 3. Materialize assets

To materialize your assets:

1. In a browser, navigate to the URL of the Dagster server that you started earlier.
2. Navigate to **Deployment**.
3. Click Reload definitions.
4. Click **Assets**, then click "View global asset lineage" to see all of your assets.

   ![2048 resolution](/images/tutorial/etl-tutorial/etl-tutorial-first-asset-lineage.png)

5. Click materialize all.
6. Navigate to the runs tab and select the most recent run. Here you can see the logs from the run.
   ![2048 resolution](/images/tutorial/etl-tutorial/first-asset-run.png)

## Next steps

- Continue this tutorial with your [asset dependencies](/etl-pipeline-tutorial/create-and-materialize-a-downstream-asset)
