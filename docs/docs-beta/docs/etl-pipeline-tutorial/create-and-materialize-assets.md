---
title: Create and materialize assets
description: Load project data and create and materialize assets
last_update:
  author: Alex Noonan
sidebar_position: 20
---


In the first step of the tutorial, you created your Dagster project with the raw data files. In this step, you will:
- Create your initial Definitions object
- Add a DuckDB resource
- Build software-defined assets
- Materialize your assets

## 1. Create a definitions object

In Dagster, the [Definitions API docs](/todo) object is where you define and organize various components within your project, such as assets and resources.

Open the `definitions.py` file in the `etl_tutorial` directory and copy the following code into it:

  ```python
  import json
  import os

  from dagster_duckdb import DuckDBResource

  import dagster as dg

  defs = dg.Definitions(
    assets=[],
    resources={},
  )
  ```

## 2. Define the DuckDB resource

In Dagster, [Resources API docs](/todo) are the external services, tools, and storage backends you need to do your job. For the storage backend in this project, we'll use [DuckDB](https://duckdb.org/), a fast, in-process SQL database that runs inside your application. We'll define it once in the definitions object, making it available to all assets and objects that need it.

  ```python
  defs = dg.Definitions(
      assets=[],
      resources={"duckdb": DuckDBResource(database="data/mydb.duckdb")},
  )
  ```

## 3. Create assets

Software defined [assets API docs](/todo) are the main building blocks in Dagster. An asset is composed of three components:
1. Asset key or unique identifier.
2. An op which is a function that is invoked to produce the asset.
3. Upstream dependencies that the asset depends on. 

You can read more about our philosophy behind the [asset centric approach](https://dagster.io/blog/software-defined-assets).

### Products asset

First, we will create an asset that creates a DuckDB table to hold data from the products CSV. This asset takes the `duckdb` resource defined earlier and returns a <PyObject section="assets" module="dagster" object="MaterializeResult" /> object.
Additionally, this asset contains metadata in the <PyObject section="assets" module="dagster" object="asset" decorator /> decorator parameters to help categorize the asset, and in the `return` block to give us a preview of the asset in the Dagster UI.

To create this asset, open the `definitions.py` file and copy the following code into it:

<CodeExample filePath="guides/tutorials/etl_tutorial/etl_tutorial/definitions.py" language="python" lineStart="8" lineEnd="33"/>

### Sales reps asset

The code for the sales reps asset is similar to the product asset code. In the `definitions.py` file, copy the following code below the product asset code:

<CodeExample filePath="guides/tutorials/etl_tutorial/etl_tutorial/definitions.py" language="python" lineStart="35" lineEnd="61"/>

### Sales data asset

To add the sales data asset, copy the following code into your `definitions.py` file below the sales reps asset:

<CodeExample filePath="guides/tutorials/etl_tutorial/etl_tutorial/definitions.py" language="python" lineStart="62" lineEnd="87"/>

## 4. Add assets to the definitions object

Now to pull these assets into our Definitions object. Adding them to the Definitions object makes them available to the Dagster project. Add them to the empty list in the assets parameter.

  ```python
  defs = dg.Definitions(
      assets=[products,
          sales_reps,
          sales_data,
      ],
      resources={"duckdb": DuckDBResource(database="data/mydb.duckdb")},
  )
  ```

## 5. Materialize assets

To materialize your assets:
1. In a browser, navigate to the URL of the Dagster server that yous started earlier. 
2. Navigate to **Deployment**.
3. Click Reload definitions.
4. Click **Assets**, then click "View global asset lineage" to see all of your assets.

   ![2048 resolution](/images/tutorial/etl-tutorial/etl-tutorial-first-asset-lineage.png)

5. Click materialize all.
6. Navigate to the runs tab and select the most recent run. Here you can see the logs from the run. 
   ![2048 resolution](/images/tutorial/etl-tutorial/first-asset-run.png)


## Next steps

- Continue this tutorial with your [asset dependencies](create-and-materialize-a-downstream-asset)
