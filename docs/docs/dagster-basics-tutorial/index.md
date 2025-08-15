---
title: Build a Dagster Pipeline
description: Learn how to build a pipeline with Dagster
last_update:
  author: Dennis Hume
sidebar_class_name: hidden
canonicalUrl: '/dagster-basics-tutorial'
slug: '/dagster-basics-tutorial'
---

# Build your first Dagster pipeline

In this tutorial you will learn to:

- Set up a Dagster project with the recommended project structure
- Create and materialize assets and dependencies
- Ensure data quality with asset checks
- Create and materialize partitioned assets
- Automate the pipeline

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
         uvx -U create-dagster project dagster-tutorial
         ```

      2. Respond `y` to the prompt to run `uv sync` after scaffolding

         ![Responding y to uv sync prompt](/images/getting-started/quickstart/uv_sync_yes.png)

      3. Change to the `dagster-tutorial` directory:

         ```shell
         cd dagster-tutorial
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
         create-dagster project dagster-tutorial
         ```
      2. Change to the `dagster-tutorial` directory:

         ```shell
         cd dagster-tutorial
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

![2048 resolution](/images/tutorial/dagster-tutorial/empty-project.png)

## Next steps

- Continue this tutorial with [extract data](/etl-pipeline-tutorial/extract-data)
