---
title: "Set up the dbt project"
description: Dagster can orchestrate dbt alongside other technologies.
sidebar_position: 100
---

In this part of the tutorial, you will:

- [Download a dbt project](#step-1-download-the-sample-dbt-project)
- [Configure your dbt project to run with DuckDB](#step-2-configure-your-dbt-project-to-run-with-duckdb)
- [Build your dbt project](#step-3-build-your-dbt-project)

## Step 1: Download the sample dbt project

Let's get started by downloading a sample dbt project. We'll use the standard dbt [Jaffle Shop](https://github.com/dbt-labs/jaffle_shop) example.

1. First, create a folder that will ultimately contain both your dbt project and Dagster code.

   ```shell
   mkdir tutorial-dbt-dagster
   ```

2. Then, navigate into that folder:

   ```shell
   cd tutorial-dbt-dagster
   ```

3. Finally, download the sample dbt project into that folder.

   ```shell
   git clone https://github.com/dbt-labs/jaffle_shop.git
   ```

## Step 2: Configure your dbt project to run with DuckDB

Running dbt requires a data warehouse to store the tables that are created from the dbt models. For our data warehouse, we'll use DuckDB, because setting it up doesn't require any long-running services or external infrastructure.

You'll set up dbt to work with DuckDB by configuring a dbt [profile](https://docs.getdbt.com/docs/core/connect-data-platform/connection-profiles):

1. Navigate into the `jaffle_shop` folder, which was created when you downloaded the project, inside your `tutorial-dbt-dagster` folder:

   ```shell
   cd jaffle_shop
   ```

2. In this folder, with your text editor of choice, create a file named `profiles.yml` and add the following code to it:

   ```yaml
   jaffle_shop:
     target: dev
     outputs:
       dev:
         type: duckdb
         path: tutorial.duckdb
         threads: 24
   ```

## Step 3: Build your dbt project

With the profile configured above, your dbt project should now be usable. To test it out, run:

```shell
dbt build
```

This will run all the models, seeds, and snapshots in the project and store a set of tables in your DuckDB database.

:::note

For other dbt projects, you may need to run additional commands before building the project. For instance, a project with [dependencies](https://docs.getdbt.com/docs/collaborate/govern/project-dependencies) will require you to run [`dbt deps`](https://docs.getdbt.com/reference/commands/deps) before building the project. For more information, see the [official dbt Command reference page](https://docs.getdbt.com/reference/dbt-commands).

:::note

## What's next?

At this point, you should have a fully-configured dbt project that's ready to work with Dagster. The next step is to [load the dbt models into Dagster as assets](load-dbt-models).
