---
title: Dagster & dbt (Pythonic)
sidebar_label: dbt (Pythonic)
description: Orchestrate dbt models.
sidebar_position: 100
---

:::note

If you are just getting started with the dbt integration, we recommend using the new [dbt component](/integrations/libraries/dbt).

:::

Dagster orchestrates dbt alongside other technologies, so you can schedule dbt with Spark, Python, etc. in a single data pipeline. Dagster's asset-oriented approach allows Dagster to understand dbt at the level of individual dbt models.

## 1. Prepare a Dagster project

To begin, you'll need a Dagster project. You can use an [existing components-ready project](/guides/build/projects/moving-to-components/migrating-project) or create a new one:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/dbt-component/1-scaffold-project.txt" />

Activate the project virtual environment:

<CliInvocationExample contents="source .venv/bin/activate" />

Then, add the `dagster-dbt` library to the project, along with a duckdb adapter:

<PackageInstallInstructions packageName="dagster-dbt dbt-duckdb" />

## 2. Set up a dbt project

For this tutorial, we'll use the jaffle shop dbt project as an example. Clone it into your project:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/dbt-component/3-jaffle-clone.txt" />

We will create a `profiles.yml` file in the `dbt` directory to configure the project to use DuckDB:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/integrations/dbt-component/4-profiles.yml"
  title="dbt/profiles.yml"
  language="yaml"
/>

## 3. Initialize the dbt assets

First create a dbt resource. This will point to the dbt project directory within the Dagster project directory:

<CodeExample
  path="docs_snippets/docs_snippets/integrations/dbt/pythonic/resources.py"
  title="my_project/defs/resources.py"
  language="python"
/>

With the dbt resource defined, you can use the dbt project to generate the dbt assets:

<CodeExample
  path="docs_snippets/docs_snippets/integrations/dbt/pythonic/assets.py"
  title="my_project/defs/assets.py"
  language="python"
/>

## 4. Run your dbt models

To execute your dbt models, you can use the `dg launch` command to kick off a run through the CLI:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/dbt-component/9-dbt-run.txt" />

## 5. Customize dbt assets

You can customize the properties of the assets emitted by each dbt model using a `DagsterDbtTranslator`. This allows you to modify asset metadata such as group names, descriptions, and other properties. To create a custom translator, create a new class that inherits from `DagsterDbtTranslator`. You can then write custom logic for metadata attributes of the dbt assets by overriding the `get_asset_key` and `get_group_name` methods. The translator is then applied to the `@dbt_assets` assets:

<CodeExample
  path="docs_snippets/docs_snippets/integrations/dbt/pythonic/assets_translator.py"
  title="my_project/defs/assets.py"
  language="python"
/>

## 6. Handling incremental models

If you have incremental models in your dbt project, you can model these as partitioned assets, and update the command that is used to run the dbt models to pass in `--vars` based on the range of partitions that are being processed.

To enable partitioning for incremental dbt models in Dagster, we start by creating a new `@dbt_assets` definition. First, we add a selector (`INCREMENTAL_SELECTOR`) to identify incremental models and configure them with a `daily_partition`. This allows Dagster to determine which partition is running and pass the correct time window (min_date, max_date) into dbt using the vars argument. With this setup, dbt builds only the records within the active partition.

Next, we separate our dbt executions: one `@dbt_assets` function (`dbt_analytics`) excludes incremental models, while another (`incremental_dbt_models`) handles only those incremental assets with partitions. Inside `incremental_dbt_models`, we fetch the partition time window from the context, format it as variables, and pass them into dbt’s CLI command. This ensures dbt materializes only the partition-specific slice of data while keeping dependencies clear and maintainable.

<CodeExample
  path="docs_snippets/docs_snippets/integrations/dbt/pythonic/assets_incrementals.py"
  title="my_project/defs/assets.py"
  language="python"
/>
