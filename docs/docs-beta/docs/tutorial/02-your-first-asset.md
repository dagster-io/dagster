---
title: Your First Asset 
description: Get the project data and create your first Asset
last_update:
  date: 2024-10-16
  author: Alex Noonan
---

# Your First Software Defined Asset

Now that we have the raw data files and the Dagster project setup lets create some loading those csv's into duckdb. 

Asset definitions enable a declarative approach to data management, in which code is the source of truth on what data assets should exist and how those assets are computed.

<iframe width="560" height="315" src="https://www.youtube.com/embed/In4CUoFKOfY?si=Xnk_CADS1pf7D5BA" title="YouTube video player" frameborder="0" allow="accelerometer; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>

## What you'll learn

- Creating our initial definitions object
- Adding a duckdb resource
- Building some basic software defined assets 

## Building definitions object

The definitions object [need docs reference] in Dagster serves as the central configuration point for defining and organizing various components within a Dagster Project. It acts as a container that holds all the necessary configurations for a code location, ensuring that everything is organized and easily accessible. 

1. Creating Definitions object and duckdb resource

Open the definitions.py file and add the following import statements and definitions object. 

  ```python
  import json
  import os

  from dagster_duckdb import DuckDBResource

  import dagster as dg

  defs = dg.Definitions(
    assets=[],
    resources={"duckdb": DuckDBResource(database="data/mydb.duckdb")},
  )
  ```

## Loading raw data

1. Products Asset

We need to create an asset that creates a duckdb table for the products csv. Additionally we should add meta data to help categorize this asset and give us a preview of what it looks like in the Dagster UI. 

<CodeExample filePath="guides/tutorials/etl_tutorial/etl_tutorial/definitions.py" language="python" lineStart="8" lineEnd="33"/>

You'll notice here that we have meta data for the compute kind for this asset as well as making it part of the ingestion group. Additionally, at the end we add the row count and a preview of what the table looks like. 

2. Sales Reps Asset

This code will be very similar to the product asset but this time its focused on Sales Reps.

<CodeExample filePath="guides/tutorials/etl_tutorial/etl_tutorial/definitions.py" language="python" lineStart="35" lineEnd="61"/>

3. Sales Data Asset

Same thing for Sales Data

<CodeExample filePath="guides/tutorials/etl_tutorial/etl_tutorial/definitions.py" language="python" lineStart="62" lineEnd="87"/>

4. Bringing our assets into the Definitions object

Now to pull these assets into our definitions object, add them to the empty list in the assets parameter. 

  ```python
  defs = dg.Definitions(
    assets=[products,
        sales_reps,
        sales_data,
    ],
    resources={"duckdb": DuckDBResource(database="data/mydb.duckdb")}
    ),
  ```

## Materialize Assets

Lets fire up Dagster and materialize these assets. If you are not in the project root directory navigate there now. 

Run the `dagster dev` command. Dagster should open up in your browser. Navigate to the Global asset lineage page. You should see this

[screenshot of global asset lineage]

Click on products and then materilize. Navigate to the jobs screen. 

[screenshot of run]

Do the same for sales_reps, and sales_data. from 

## What you've learned

- Created a Dagster Definition
- Built our ingestion assets


## Next steps

- Continue this tutorial with your [Asset Dependencies](/tutorial/02-your-first-asset)