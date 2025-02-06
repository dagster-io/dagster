---
title: "Migrating an Airflow PythonOperator to Dagster"
sidebar_position: 300
---

In this page, we'll explain migrating an Airflow `PythonOperator` to Dagster.

## About the Airflow PythonOperator

In Airflow, the `PythonOperator` runs arbitrary Python functions. For example, you might have a task that runs a function `write_to_db`, which combs a directory for files, and writes each one to a db table.

<CodeExample path="docs_snippets/docs_snippets/integrations/airlift/operator_migration/python_operator.py" starAfter="start_op" endBefore="end_op" />

## Dagster equivalent

The Dagster equivalent is instead to construct a <PyObject section="assets" object="asset" module="dagster"/> or <PyObject section="assets" object="multi_asset" module="dagster"/>-decorated function, which materializes assets corresponding to what your python function is doing.

<CodeExample path="docs_snippets/docs_snippets/integrations/airlift/operator_migration/pyop_multi_asset_complete.py" starAfter="start_asset" endBefore="end_asset" />

## Migrating the operator

Migrating the operator breaks down into a few steps:

1. Make a shared library available to both Airflow and Dagster with your python function.
2. Writing an `@asset`-decorated function which runs the python function shared between both modules.
3. Using `dagster-airlift` to proxy execution of the original task to Dagster.

### Step 1: Building a shared library

We recommend a monorepo setup for migration; this allows you to keep all your code in one place and easily share code between Airflow and Dagster, without complex CI/CD coordination.

First, we recommend factoring out a shared package to be available to both the Dagster runtime and the Airflow runtime which contains your python function. The process is as follows:

1. Scaffold out a new python project which will contain your shared infrastructure.
2. Ensure that the shared library is available to both your Airflow and Dagster deployments. This can be done by adding an editable requirement to your `setup.py` or `pyproject.toml` file in your Airflow/Dagster package.
3. Include the python dependencies relevant to your particular function in your new package. Write your python function in the shared package, and change your Airflow code to import the function from the shared library.

To illustrate what this might look like a bit more; let's say you originally have this project structure in Airflow:

```plaintext
airflow_repo/
├── airflow_package/
│   └── dags/
│       └── my_dag.py  # Contains your Python function
```

With dag code that looks this:

<CodeExample path="docs_snippets/docs_snippets/integrations/airlift/operator_migration/python_operator.py" starAfter="start_op" endBefore="end_op" />

You might create a new top-level package to contain the shared code:

```plaintext
airflow_repo/
├── airflow_package/
│   └── dags/
│       └── my_dag.py  # Imports the python function from shared module.
├── shared-package/
│   └── shared_package/
│       └── shared_module.py  # Contains your Python function
```

And then import the function from the shared package in Airflow:

<CodeExample path="docs_snippets/docs_snippets/integrations/airlift/operator_migration/python_operator.py" starAfter="start_shared" endBefore="end_shared" />

The reason we recommend using a separate `shared` package is to help ensure that there aren't dependency conflicts between Airflow and Dagster as you migrate. Airflow has very complex dependency management, and migrating to Dagster gives you an opportunity to clean up and isolate your dependencies. You can do this with a series of shared packages in the monorepo, which will eventually be isolated code locations in Dagster.

### Step 2: Writing an `@asset`-decorated function

Next, you can write a Dagster <PyObject section="assets" object="asset" module="dagster"/> or <PyObject section="assets" object="multi_asset" module="dagster"/>-decorated function that runs your python function. This will generally be pretty straightforward for a `PythonOperator` migration, as you can generally just invoke the shared function into the `asset` function.

<CodeExample path="docs_snippets/docs_snippets/integrations/airlift/operator_migration/pyop_asset_shared.py" />

### Step 3: Using `dagster-airlift` to proxy execution

Finally, you can use `dagster-airlift` to proxy the execution of the original task to Dagster. For more information, see "[Migrating from Airflow to Dagster](/integrations/libraries/airlift/airflow-to-dagster).