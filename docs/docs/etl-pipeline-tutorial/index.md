---
title: Build an ETL Pipeline
description: Learn how to build an ETL pipeline with Dagster
last_update:
  author: Alex Noonan
sidebar_class_name: hidden
---

# Build your first ETL pipeline

In this tutorial, you'll build an ETL pipeline with Dagster that:

- Imports sales data to DuckDB
- Transforms data into reports
- Runs scheduled reports automatically
- Generates one-time reports on demand

## You will learn to:

- Set up a Dagster project with the recommended project structure
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
- Familiarity with SQL and Python data manipulation libraries, such as Pandas.
- Understanding of data pipelines and the extract, transform, and load process.

</details>

## Step 1: Set up your Dagster environment

First, set up a new Dagster project.

1. Open your terminal and scaffold a new project with `dg`:

   ```bash
   dg init --project-name dagster_tutorial --python-environment uv_managed
   ```

2. Change into that project

  ```bash
  cd dagster_tutorial
  ```

2. Activate the project virtual environment:

   <Tabs>
     <TabItem value="macos" label="MacOS">
       ```source dagster_tutorial/bin/activate ```
     </TabItem>
     <TabItem value="windows" label="Windows">
       ```dagster_tutorial\Scripts\activate ```
     </TabItem>
   </Tabs>

3. Install Dagster and the required dependencies:

   ```bash
   uv pip install pandas dagster-duckdb
   ```

4. Check the project structure:

  ```bash
  dg check defs
  ```

## Step 2: Create the Dagster project structure

Run the following command to create the project directories and files for this tutorial:

```bash
dagster project from-example --example getting_started_etl_tutorial
```

```
.
├── pyproject.toml
├── src
│   └── dagster_tutorial
│       ├── __init__.py
│       ├── definitions.py
│       ├── defs
│       │   └── __init__.py
│       └── lib
│           └── __init__.py
└── tests
    └── __init__.py
```

:::info
Dagster has several example projects you can install depending on your use case. To see the full list, run `dagster project list-examples`. For more information on the `dagster project` command, see the [API documentation](https://docs-preview.dagster.io/api/cli#dagster-project).
:::

## Step 3: Launch the Dagster webserver

To make sure Dagster and its dependencies were installed correctly, navigate to the project root directory and start the Dagster webserver:"

```bash
dg dev
```

## Next steps

- Continue this tutorial by [creating and materializing assets](/etl-pipeline-tutorial/create-and-materialize-assets)
