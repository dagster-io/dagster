---
title: Build an ETL Pipeline
description: Learn how to build an ETL pipeline with Dagster
last_update:
  author: Alex Noonan
sidebar_class_name: hidden
---

# Build your first ETL pipeline

In this tutorial, you'll build an ETL pipeline with Dagster that:

- Imports sales data to DuckDB using Sling
- Transforms data into reports with dbt
- Runs scheduled reports automatically
- Generates one-time reports on demand
- Visualize the data with Evidence

## You will learn to:

- Set up a Dagster project with the recommended project structure
- Integrate with other tools
- Create and materialize assets
- Create and materialize dependant assets
- Ensure data quality with asset checks
- Create and materialize partitioned assets
- Automate the pipeline
- Create and materialize a sensor asset
- Refactor your project when it becomes more complex

<details>
  <summary>Prerequisites</summary>

To follow the steps in this guide, you'll need:

- Basic Python knowledge
- Python 3.9+ installed on your system. Refer to the [Installation guide](/getting-started/installation) for information.
- Familiarity with SQL and Python.
- Understanding of data pipelines and the extract, transform, and load process.

</details>

## Step 1: Set up your Dagster environment

First, set up a new Dagster project.

1. Open your terminal and scaffold a new project with `dg`:

   ```bash
   uvx create-dagster project etl-tutorial-components
   ```

2. Change into that project

  ```bash
  cd etl-tutorial-components
  ```

3. Activate the project virtual environment:

   <Tabs>
     <TabItem value="macos" label="MacOS">
       ```source .venv/bin/activate ```
     </TabItem>
     <TabItem value="windows" label="Windows">
       ```.venv\Scripts\activate ```
     </TabItem>
   </Tabs>

4. Install Dagster and the required dependencies:

   ```bash
   uv pip install dagster-duckdb dagster-dbt dagster-sling dagster-evidence dagster-webserver
   ```

5. Check the project structure:

  ```bash
  dg check defs
  ```

## Step 2: Launch the Dagster webserver

To make sure Dagster and its dependencies were installed correctly, navigate to the project root directory and start the Dagster webserver:"

```bash
dg dev
```

At this point the project will be empty but we will continue to add to it throughout the tutorial.

## Next steps

- Continue this tutorial by [creating and materializing assets](/etl-pipeline-tutorial/create-and-materialize-assets)
