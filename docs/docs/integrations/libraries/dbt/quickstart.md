---
title: Quickstart
description: Get started using dbt with Dagster to schedule dbt alongside other technologies in a single data pipeline.
sidebar_position: 100
---

Dagster orchestrates dbt alongside other technologies, so you can schedule dbt with Spark, Python, etc. in a single data pipeline. Dagster's asset-oriented approach allows Dagster to understand dbt at the level of individual dbt models.

<details>
  <summary>Prerequisites</summary>

To follow the steps in this guide, you'll need:

- A basic understanding of dbt, DuckDB, and Dagster concepts such as [assets](/guides/build/assets) and [resources](/guides/build/external-resources)

</details>

## Create a new Dagster project

<Tabs groupId="package-manager">
   <TabItem value="uv" label="uv">
      1. Open your terminal and scaffold a new Dagster project:

         ```shell
         uvx -U create-dagster project dagster-dbt-quickstart
         ```

      2. Respond `y` to the prompt to run `uv sync` after scaffolding

         ![Responding y to uv sync prompt](/images/getting-started/quickstart/uv_sync_yes.png)

      3. Change to the `dagster-dbt-quickstart` directory:

         ```shell
         cd dagster-dbt-quickstart
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
         create-dagster project dagster-dbt-quickstart
         ```
      2. Change to the `dagster-dbt-quickstart` directory:

         ```shell
         cd dagster-dbt-quickstart
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

Next install the following packages:

<PackageInstallInstructions packageName="duckdb plotly pandas dagster-dbt dbt-duckdb" />

## Add a basic dbt project

Within the Dagster project, download this basic dbt project into the `src` directory, which includes a few models and a DuckDb backend:

```bash
git clone https://github.com/dagster-io/basic-dbt-project src/basic-dbt-project
```

The structure of the dbt project should look like this:

```
src/basic-dbt-project
├── dbt_project.yml
├── models
│   └── example
│       ├── my_first_dbt_model.sql
│       ├── my_second_dbt_model.sql
│       └── schema.yml
├── profiles.yml
└── README.md
```

## Scaffold the dbt component

Next we will scaffold the dbt component:

```bash
dg scaffold defs dagster_dbt.DbtProjectComponent transform --project-path src/basic-dbt-project
```

This generates a YAML configuration based on the dbt project path. No further changes are needed in defs.yaml, which will look like this:

<CodeExample
  path="docs_snippets/docs_snippets/guides/etl/transform-dbt/defs.yaml"
  language="python"
  title="src/dagster_dbt_quickstart/defs/transform/defs.yaml"
/>

## Adding upstream dependencies

Often, you'll want Dagster to generate data that will be used by downstream dbt models. To do this, scaffold an `assets.py` where custom assets can be defined:

```bash
dg scaffold defs dagster.asset assets.py
```

Then add an upstream asset:

<CodeExample
  path="docs_snippets/docs_snippets/guides/etl/transform-dbt/assets.py"
  language="python"
  title="src/dagster_dbt_quickstart/defs/assets.py"
  startAfter="start_upstream_asset"
  endBefore="end_upstream_asset"
/>

Next, add a dbt model that will source the `raw_customers` asset and define the dependency for Dagster. Create the dbt model:

<CodeExample
  path="docs_snippets/docs_snippets/guides/etl/transform-dbt/basic-dbt-project/models/example/customers.sql"
  language="sql"
  title="dagster_dbt_quickstart/src/basic-dbt-project/models/example/customers.sql"
/>

Next, create a `_source.yml` file that points dbt to the upstream `raw_customers` asset:

<CodeExample
  path="docs_snippets/docs_snippets/guides/etl/transform-dbt/basic-dbt-project/models/example/_source.yml"
  language="yaml"
  title="dagster_dbt_quickstart/src/basic-dbt-project/models/example/_source.yml"
/>

![Screenshot of dbt lineage](/images/integrations/dbt/dbt-lineage-1.png)

## Adding downstream dependencies

You may also have assets that depend on the output of dbt models. Within the `assets.py` file, create an asset that depends on the result of the new `customers` model. This asset will create a histogram of the first names of the customers:

<CodeExample
  path="docs_snippets/docs_snippets/guides/etl/transform-dbt/assets.py"
  language="python"
  title="src/dagster_dbt_quickstart/defs/assets.py"
  startAfter="start_downstream_asset"
  endBefore="end_downstream_asset"
/>

![Screenshot of dbt lineage](/images/integrations/dbt/dbt-lineage-2.png)

## Scheduling dbt models

You can schedule your dbt models using Dagster [schedules](/guides/automate/schedules). First scaffold a schedule:

```bash
dg scaffold defs dagster.schedule schedules.py
```

Then you can update the schedule cron syntax:

<CodeExample
  path="docs_snippets/docs_snippets/guides/etl/transform-dbt/schedules.py"
  language="python"
  title="Scheduling our dbt models"
/>
