---
description: Migrating an Airflow `BashOperator` to Dagster.
sidebar_position: 1000
title: Migrating an Airflow BashOperator to Dagster
---

import AirliftPreview from '@site/docs/partials/\_AirliftPreview.md';

<AirliftPreview />

The Airflow `BashOperator` is used to execute bash commands as part of a data pipeline.

<CodeExample path="docs_snippets/docs_snippets/integrations/airlift/operator_migration/bash_operator_general.py" />

The `BashOperator`'s functionality is very general, since it can be used to run any bash command, and there exist richer integrations in Dagster for many common BashOperator use cases. In this guide, we'll explain how to migrate the `BashOperator` to execute a bash command in Dagster, and how to use the `dagster-airlift` library to proxy the execution of the original task to Dagster. We'll also provide a reference for richer integrations in Dagster for common BashOperator use cases.

:::note

If you're using the `BashOperator` to execute dbt commands, see "[Migrating an Airflow BashOperator (dbt) to Dagster](/guides/migrate/airflow-to-dagster/airflow-operator-migration/bash-operator-dbt)".

:::

## Dagster equivalent

The direct Dagster equivalent to the `BashOperator` is the <PyObject section="pipes" object="PipesSubprocessClient" module="dagster"/>, which you can use to execute a bash command in a subprocess.

## Migrating the operator

To migrate the operator, you will need to:

1. Ensure that the resources necessary for your bash command are available to both your Airflow and Dagster deployments.
2. Write an <PyObject section="assets" object="asset" module="dagster"/> that executes the bash command using the <PyObject section="pipes" object="PipesSubprocessClient" module="dagster"/>.
3. Use `dagster-airlift` to proxy execution of the original task to Dagster.
4. (Optional) Implement a richer integration for common BashOperator use cases.

### Step 1: Ensure shared bash command access in Airflow and Dagster

First, you'll need to ensure that the bash command you're running is available for use in both your Airflow and Dagster deployments. What this entails will vary depending on the command you're running. For example, if you're running a Python script, you will need to ensure the Python script exists in a shared location accessible to both Airflow and Dagster, and all necessary environment variables are set in both environments.

### Step 2: Write an `@asset` that executes the bash command

You can write a Dagster <PyObject section="assets" object="asset" module="dagster"/>-decorated function that runs your bash command. This is straightforward with the <PyObject section="pipes" object="PipesSubprocessClient" module="dagster"/>:

<CodeExample path="docs_snippets/docs_snippets/integrations/airlift/operator_migration/using_pipes_subprocess.py" />

### Step 3: Use `dagster-airlift` to proxy execution

Finally, you can use `dagster-airlift` to proxy the execution of the original task to Dagster. 
{/* TODO update this sentence, link to appropriate guide */}

### (Optional) Step 4: Implement richer integrations

For many of the use cases that you might be using the BashOperator for, Dagster might have better options. We'll detail some of those here.

#### Running a Python script

As mentioned above, you can use the <PyObject section="pipes" object="PipesSubprocessClient" module="dagster"/> to run a Python script in a subprocess. You can also modify this script to send additional information and logging back to Dagster. For more information, see the [Dagster Pipes documentation](/guides/build/external-pipelines/).

#### Running a dbt command

If you're using the `BashOperator` to execute dbt commands, you can follow the steps in "[Migrating an Airflow BashOperator (dbt) to Dagster](/guides/migrate/airflow-to-dagster/airflow-operator-migration/bash-operator-dbt)" to switch from the `BashOperator` to the `dagster-dbt` integration.

#### Running S3 Sync or other AWS CLI commands

Dagster has a rich set of integrations for AWS services. For example, you can use the <PyObject section="libraries" object="s3.S3Resource" module="dagster_aws"/> to interact with S3 directly. For more information, see the [AWS integration documentation](/integrations/libraries/aws).
