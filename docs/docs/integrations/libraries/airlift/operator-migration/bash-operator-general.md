---
title: "Migrating an Airflow BashOperator to Dagster"
sidebar_position: 100
---

In this page, we'll explain migrating an Airflow `BashOperator` to Dagster.

:::note

If using the `BashOperator` to execute dbt commands, see "[Migrating an Airflow BashOperator (dbt) to Dagster](bash-operator-dbt)".

:::

## About the Airflow BashOperator

The Airflow `BashOperator` is a common operator used to execute bash commands as part of a data pipeline.

<CodeExample path="docs_snippets/docs_snippets/integrations/airlift/operator_migration/bash_operator_general.py" />

The `BashOperator`'s functionality is very general since it can be used to run any bash command, and there exist richer integrations in Dagster for many common BashOperator use cases. We'll explain how 1-1 migration of the BashOperator to execute a bash command in Dagster, and how to use the `dagster-airlift` library to proxy the execution of the original task to Dagster. We'll also provide a reference for richer integrations in Dagster for common BashOperator use cases.

## Dagster equivalent

The direct Dagster equivalent to the `BashOperator` is to use the <PyObject section="pipes" object="PipesSubprocessClient" module="dagster"/> to execute a bash command in a subprocess.

## Migrating the operator

Migrating the operator breaks down into a few steps:

1. Ensure that the resources necessary for your bash command are available to both your Airflow and Dagster deployments.
2. Write an <PyObject section="assets" object="asset" module="dagster"/> that executes the bash command using the <PyObject section="pipes" object="PipesSubprocessClient" module="dagster"/>.
3. Use `dagster-airlift` to proxy execution of the original task to Dagster.
4. (Optional) Implement a richer integration for common BashOperator use cases.

### Step 1: Ensure shared bash command access

First, you'll need to ensure that the bash command you're running is available for use in both your Airflow and Dagster deployments. What this entails will vary depending on the command you're running. For example, if you're running a Python script, it's as simple as ensuring the Python script exists in a shared location accessible to both Airflow and Dagster, and all necessary env vars are set in both environments.

### Step 2: Writing an `@asset`-decorated function

You can write a Dagster <PyObject section="assets" object="asset" module="dagster"/>-decorated function that runs your bash command. This is quite straightforward using the <PyObject section="pipes" object="PipesSubprocessClient" module="dagster"/>.

<CodeExample path="docs_snippets/docs_snippets/integrations/airlift/operator_migration/using_pipes_subprocess.py" />

### Step 3: Using dagster-airlift to proxy execution

Finally, you can use `dagster-airlift` to proxy the execution of the original task to Dagster. For more information, see "[Migrating from Airflow to Dagster](/integrations/libraries/airlift/airflow-to-dagster).

### Step 4: Implementing richer integrations

For many of the use cases that you might be using the BashOperator for, Dagster might have better options. We'll detail some of those here.

#### Running a Python script

As mentioned above, you can use the <PyObject section="pipes" object="PipesSubprocessClient" module="dagster"/> to run a Python script in a subprocess. But you can also modify this script to send additional information and logging back to Dagster. See the [Dagster Pipes tutorial](/guides/build/external-pipelines/) for more information.

#### Running a dbt command

We have a whole guide for switching from the `BashOperator` to the `dbt` integration in Dagster. For more information, see "[Migrating an Airflow BashOperator (dbt) to Dagster](bash-operator-dbt)".

#### Running S3 Sync or other AWS CLI commands

Dagster has a rich set of integrations for AWS services. For example, you can use the <PyObject section="libraries" object="s3.S3Resource" module="dagster_aws"/> to interact with S3 directly.
