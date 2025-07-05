---
title: Build an ETL Pipeline
description: Learn how to build an ETL pipeline with Dagster
last_update:
  author: Alex Noonan
sidebar_class_name: hidden
---

# Build your first ETL pipeline

In this tutorial, you'll build a full ETL pipeline with Dagster that:

- Ingests data into [DuckDB](https://duckdb.org)
- Transforms data into reports with [dbt](https://www.getdbt.com)
- Runs scheduled reports automatically
- Generates one-time reports on demand
- Visualizes the data with [Evidence](https://evidence.dev/)

You will learn to:

- Set up a Dagster project with the recommended project structure
- Integrate with other tools
- Create and materialize assets and dependencies
- Ensure data quality with asset checks
- Create and materialize partitioned assets
- Automate the pipeline
- Create and materialize assets with sensors

## Prerequisites

To follow the steps in this tutorial, you'll need:

* Python 3.9+ and [`uv`](https://docs.astral.sh/uv) installed. For more information, see the [Installation guide](/getting-started/installation).
* Familiarity with Python and SQL.
* A basic understanding of data pipelines and the extract, transform, and load (ETL) process.

## Set up your Dagster project

1. Open your terminal and scaffold a new project with `uv`:

   <CliInvocationExample path="docs_snippets/docs_snippets/guides/tutorials/etl_tutorial/commands/uvx-create.txt" />

2. Change directory into your new project:

   <CliInvocationExample contents="cd etl-tutorial" />

3. Activate the project virtual environment:

   <Tabs>
     <TabItem value="macos" label="MacOS">
       ```source .venv/bin/activate ```
     </TabItem>
     <TabItem value="windows" label="Windows">
       ```.venv\Scripts\activate ```
     </TabItem>
   </Tabs>


4. To make sure Dagster and its dependencies were installed correctly, start the Dagster webserver:

   <CliInvocationExample contents="dg dev" />

   In your browser, navigate to [http://127.0.0.1:3000](http://127.0.0.1:3000)

   At this point the project will be empty, but we will continue to add to it throughout the tutorial.

   ![2048 resolution](/images/tutorial/etl-tutorial/empty-project.png)

## Next steps

- Continue this tutorial with [extract data](/etl-pipeline-tutorial/extract-data)
