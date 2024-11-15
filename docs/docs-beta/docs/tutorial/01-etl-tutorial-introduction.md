---
title: Build an ETL Pipeline
description: Learn how to build an ETL pipeline with Dagster
last_update:
  author: Alex Noonan
---

# Build your first ETL pipeline

In this tutorial, you'll build an ETL pipeline with Dagster that:

1. Imports sales data to DuckDB
2. Transforms data into reports
3. Runs scheduled reports automatically
4. Generates one-time reports on demand

## What you'll learn

- Setting up a Dagster project with the recommended project structure
- Creating Assets with metadata
- Using Resources to connect to external systems
- Building dependencies between assets
- Running a pipeline by materializing assets
- Adding schedules, sensors, and partitions to your assets
- Refactor project into recommended structure

[Add image for what the completed global asset graph looks like]

## Prerequisites

<details>
  <summary>Prerequisites</summary>

To follow the steps in this guide, you'll need:

- Basic Python knowledge
- Python 3.9+ installed on your system. Refer to the [Installation guide](/getting-started/installation) for information.
- Familiarity with SQL or Python data manipulation libraries (Pandas or Polars).
- Understanding of data pipelines and the extract, transform, and load process.
</details>


## Step 1: Set up your Dagster environment

First, set up a new Dagster project.

1. Open your terminal and create a new directory for your project:

   ```bash
   mkdir dagster-etl-tutorial
   cd dagster-etl-tutorial
   ```

2. Create and activate a virtual environment:

   <Tabs>
   <TabItem value="macos" label="MacOS">
   ```bash
   python -m venv dagster_tutorial
   source dagster_tutorial/bin/activate
   ```
   </TabItem>
   <TabItem value="windows" label="Windows">
   ```bash
   python -m venv dagster_tutorial
   dagster_tutorial\Scripts\activate
   ```
   </TabItem>
   </Tabs>

3. Install Dagster and the required dependencies:

   ```bash
   pip install dagster dagster-webserver pandas dagster-duckdb
   ```

## Step 2: Create the Dagster project structure

Next, you'll create the project directories and files for this tutorial with the `dagster project from-example` command:

   ```bash 
      dagster project from-example --example getting_started_etl_tutorial
   ```

Your project should have this structure:
{/* vale off */}
```
dagster-etl-tutorial/
├── data/
│   └── products.csv
│   └── sales_data.csv
│   └── sales_reps.csv
│   └── sample_request/
│       └── request.json
├── etl_tutorial/
│   └── definitions.py
├── pyproject.toml
├── setup.cfg
├── setup.py
```
{/* vale on */}

:::info
Dagster has several example projects you can install depending on your use case. To see the full list, run `dagster project list-examples`. For more information on the `dagster project` command, see the [API documentation](https://docs-preview.dagster.io/api/cli#dagster-project).
::: 

## Dagster Project Structure

In the root directory there are three configuration files that are common in Python package management. These manage dependencies and identifies the Dagster modules in the project. The `etl_tutorial` folder is where our Dagster definition for this code location exists. The data directory is where the raw data for the project is stored and we will reference these files in our software-defined assets.
### File/Directory Descriptions

#### dagster-etl-tutorial directory 

In the `dagster-etl-tutorial` root directory, there are three configuration files that are common in Python package management. These files manage dependencies and identify the Dagster modules in the project.
| File | Purpose |
|------|---------|
| pyproject.toml | This file is used to specify build system requirements and package metadata for Python projects. It is part of the Python packaging ecosystem. |
| setup.cfg | This file is used for configuration of your Python package. It can include metadata about the package, dependencies, and other configuration options. |
| setup.py | This script is used to build and distribute your Python package. It is a standard file in Python projects for specifying package details. |

#### etl_tutorial directory

main directory where you will define your assets, jobs, schedules, sensors, and resources.
| File | Purpose |
|------|---------|
| definitions.py | This file is typically used to define jobs, schedules, and sensors. It organizes the various components of your Dagster project. This allows Dagster to load the definitions in a module. |

#### data directory

The data directory contains the raw data files for the project. We will reference these files in our software-defined assets in the next step of the tutorial.

## Launch Dagster

Start the Dagster webserver from your project's root directory. If you are not in the project root directory navigate there now.

  ```bash
    cd getting_started_etl_tutorial
  ```

Run the `dagster dev` command. Dagster should open up in your browser.

## Next steps

- Continue this tutorial with [create and materialize assets](/tutorial/02-create-and-materialize-assets)
