---
title: Dagster ETL pipeline
description: Learn how to build an ETL pipeline with Dagster
last_update:
  author: Dennis Hume
sidebar_custom_props:
  logo: images/dagster-primary-mark.svg
tags: [code-example]
canonicalUrl: '/examples/full-pipelines/etl-pipeline'
slug: '/examples/full-pipelines/etl-pipeline'
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

- Python 3.9+ and [`uv`](https://docs.astral.sh/uv) installed. For more information, see the [Installation guide](/getting-started/installation).
- Familiarity with Python and SQL.
- A basic understanding of data pipelines and the extract, transform, and load (ETL) process.

## 1: Scaffold a new Dagster project

<Tabs groupId="package-manager">
   <TabItem value="uv" label="uv">
      1. Open your terminal and scaffold a new Dagster project:

         ```shell
         uvx -U create-dagster project etl-tutorial
         ```

      2. Respond `y` to the prompt to run `uv sync` after scaffolding

         ![Responding y to uv sync prompt](/images/getting-started/quickstart/uv_sync_yes.png)

      3. Change to the `etl-tutorial` directory:

         ```shell
         cd etl-tutorial
         ```
      4. Activate the virtual environment:

         <Tabs>
            <TabItem value="macos" label="MacOS/Unix">
               ```shell
               source .venv/bin/activate
               ```
            </TabItem>
            <TabItem value="windows" label="Windows">
               ```shell
               .venv\Scripts\activate
               ```
            </TabItem>
         </Tabs>

   </TabItem>

   <TabItem value="pip" label="pip">
      1. Open your terminal and scaffold a new Dagster project:

         ```shell
         create-dagster project etl-tutorial
         ```
      2. Change to the `etl-tutorial` directory:

         ```shell
         cd etl-tutorial
         ```

      3. Create and activate a virtual environment:

         <Tabs>
            <TabItem value="macos" label="MacOS/Unix">
               ```shell
               python -m venv .venv
               ```
               ```shell
               source .venv/bin/activate
               ```
            </TabItem>
            <TabItem value="windows" label="Windows">
               ```shell
               python -m venv .venv
               ```
               ```shell
               .venv\Scripts\activate
               ```
            </TabItem>
         </Tabs>

      4. Install your project as an editable package:

         ```shell
         pip install --editable .
         ```

   </TabItem>
</Tabs>

## 2: Start Dagster webserver

Make sure Dagster and its dependencies were installed correctly by starting the Dagster webserver:

<CliInvocationExample contents="dg dev" />

In your browser, navigate to [http://127.0.0.1:3000](http://127.0.0.1:3000)

At this point the project will be empty, but we will continue to add to it throughout the tutorial.

![2048 resolution](/images/tutorial/etl-tutorial/empty-project.png)

## Next steps

- Continue this tutorial with [extract data](/examples/full-pipelines/etl-pipeline/extract-data)
