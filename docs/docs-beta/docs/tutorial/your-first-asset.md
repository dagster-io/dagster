---
title: Your First Asset 
description: Get the project data and create your first Asset
last_update:
  date: 2024-10-16
  author: Alex Noonan
---

# Your First Software Defined Asset

Now that we have the raw data files and the dagster project setup lets create some loading those csv's into duckdb. 

## What you'll learn

- Creating our intial defintions object
- Adding a duckdb resource
- Building some basic software defined assets 

## Building Definitions Object

The Definitions object [need docs reference] in Dagster serves as the central configuration point for defining and organizing various componenets within a Dagster Project. It acts as a container that holds all the necessary configurations for a code location, ensuring that everything is organized and easily accessable. 

1. Creating Definitions Object and duckdb resource

Open the definitions.py file and add the following import statements and definitions object. 

  ```python
  import json
  import os

  from dagster_duckdb import DuckDBResource

  import dagster as dg

  defs = dg.Definitions(
    assets=[
    ],
    resources={"duckdb": DuckDBResource(database="data/mydb.duckdb")},
  ```

## Loading raw data

1. Products Asset

We need to create an asset that creates a duckdb table for the products csv. Additionally we should add meta data to help categorize this asset and give us a preview of what it looks like in the Dagster UI. 




## What you've learned

- Set up a Python virtual environment and installed Dagster
- Copied raw data for project


## Next steps

- Continue this tutorial with your [first asset](/tutorial/your-first-asset)