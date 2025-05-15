---
description: Migrating an Airflow `BashOperator` that runs a `dbt` command to Dagster.
sidebar_position: 2000
title: Migrating an Airflow BashOperator (dbt) to Dagster
---

import AirliftPreview from '@site/docs/partials/\_AirliftPreview.md';

<AirliftPreview />

The Airflow `BashOperator` is used to execute bash commands as part of a data pipeline.

In Airflow, you might have a `BashOperator` that runs a dbt command. For example, you might have a task that runs `dbt run` to build your dbt models:

<CodeExample path="docs_snippets/docs_snippets/integrations/airlift/operator_migration/bash_operator_dbt.py" />

## Dagster equivalent

The Dagster equivalent to using the `BashOperator` to run a dbt command is to use the `dagster-dbt` library to run commands against your dbt project:

<CodeExample path="docs_snippets/docs_snippets/integrations/airlift/operator_migration/using_dbt_assets.py" />

## Migrating the operator

To migrate the operator, you will need to:

1. Make the dbt project available to both your Airflow and Dagster deployments and build the manifest
2. Write a @dbt_asset-decorated function to run your dbt commands
3. Use `dagster-airlift` to proxy execution of the original task to Dagster

### Step 1: Make the dbt project available to your Airflow and Dagster deployments and build the manifest

First, you'll need to make the dbt project available to the Dagster runtime and build the manifest.

- If you're building your Dagster deployment in a monorepo alongside your dbt and Airflow projects, you can follow the [monorepo setup guide](/integrations/libraries/dbt/reference#deploying-a-dagster-project-with-a-dbt-project).
- If you're deploying within a separate repository, you can follow the [separate repository setup guide](/integrations/libraries/dbt/reference#deploying-a-dbt-project-from-a-separate-git-repository).

### Step 2: Write a `@dbt_asset`-decorated function to run your dbt commands

Once your dbt project is available to the Dagster runtime, you can write a function that runs your dbt commands using the <PyObject section="libraries" object="dbt_assets" module="dagster_dbt" decorator/> decorator and <PyObject section="libraries" object="DbtCliResource" module="dagster_dbt"/>. Most dbt CLI commands and flags are supported; to learn more about using `@dbt_assets`, check out the [dagster-dbt quickstart](/integrations/libraries/dbt/transform-dbt) and [reference](/integrations/libraries/dbt/reference) documentation.

### Step 3: Use `dagster-airlift` to proxy execution of the original task to Dagster

Finally, you can use `dagster-airlift` to proxy the execution of the original task to Dagster. For more information, see "[Migrate from Airflow to Dagster at the task level](/guides/migrate/airflow-to-dagster/task-level-migration)".
