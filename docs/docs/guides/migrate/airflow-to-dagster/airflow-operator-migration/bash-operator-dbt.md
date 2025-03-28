---
title: 'Migrating an Airflow BashOperator (dbt) to Dagster'
sidebar_position: 200
---

In this page, we'll explain migrating an Airflow `BashOperator` that runs a `dbt` command to Dagster.

## About the Airflow BashOperator

In Airflow, you might have a `BashOperator` that runs a `dbt` command. For example, you might have a task that runs `dbt run` to build your dbt models.

<CodeExample path="docs_snippets/docs_snippets/integrations/airlift/operator_migration/bash_operator_dbt.py" />

## Dagster equivalent

The Dagster equivalent is to instead use the `dagster-dbt` library to run commands against your dbt project. Here would be the equivalent code in Dagster:

<CodeExample path="docs_snippets/docs_snippets/integrations/airlift/operator_migration/using_dbt_assets.py" />

## Migrating the operator

Migrating the operator breaks down into a few steps:

1. Making the dbt project available to both your Airflow and Dagster deployments.
2. Writing a @dbt_asset-decorated function which runs your dbt commands.
3. Using `dagster-airlift` to proxy execution of the original task to Dagster.

### Step 1: Making the dbt project available & building manifest

First, you'll need to make the dbt project available to the Dagster runtime and build the manifest.

- If you're building your Dagster deployment in a monorepo alongside your dbt and Airflow projects, you can follow this guide: [Monorepo setup](/integrations/libraries/dbt/reference#deploying-a-dagster-project-with-a-dbt-project).
- If you're deploying within a separate repository, you can follow this guide: [Separate repository setup](/integrations/libraries/dbt/reference#deploying-a-dbt-project-from-a-separate-git-repository). \*/}

### Step 2: Writing a @dbt_asset-decorated function

Once your dbt project is available, you can write a function that runs your dbt commands using the <PyObject section="libraries" object="dbt_assets" module="dagster_dbt"/> decorator and <PyObject section="libraries" object="DbtCliResource" module="dagster_dbt"/>. Most dbt CLI commands and flags are supported - to learn more about using `@dbt_assets`, check out the [dagster-dbt quickstart](/integrations/libraries/dbt/transform-dbt) and [reference](/integrations/libraries/dbt/reference).

### Step 3: Using dagster-airlift to proxy execution

Finally, you can use `dagster-airlift` to proxy the execution of the original task to Dagster. For more information, see "[Migrate from Airflow to Dagster at the task level](../task-level-migration/)".
