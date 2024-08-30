---
title: Transforming data with dbt
sidebar_position: 20
last_update:
  date: 2024-08-26
  author: Nick Roach
---

Dagster orchestrates dbt alongside other technologies, so you can schedule dbt with Spark, Python, etc. in a single data pipeline. Dagster's asset-oriented approach allows Dagster to understand dbt at the level of individual dbt models.

## What you'll learn

- How to import a basic dbt project into Dagster
- How to set upstream and downstream dependencies on non-dbt assets
- How to schedule your dbt assets

---

<details>
  <summary>Prerequisites</summary>

To follow the steps in this guide, you'll need:

- a basic understanding of dbt, DuckDB, and Dagster concepts such as assets and resources
- the dbt and DuckDB CLIs installed
- Dagster, DuckDB, `plotly`, `dagster-dbt`, and `dbt-duckdb` Python packages installed
</details>

---

## Setting up a basic dbt project

Start by downloading our basic dbt project:

```bash
git clone https://github.com/dagster-io/basic-dbt-project
```

This a minimal dbt project with just a couple models and a DuckDB backend. Your project structure should look like this:

```
├── README.md
├── dbt_project.yml
├── profiles.yml
├── models
│   └── example
│       ├── my_first_dbt_model.sql
│       ├── my_second_dbt_model.sql
│       └── schema.yml
```

Now we can point Dagster to our dbt project and build our asset graph. Let's create a `definitions.py` file in the same directory as our dbt project:

<CodeExample filePath="guides/etl/transform-dbt/dbt_definitions.py" language="python" title="Importing a dbt project into Dagster" />

In this file you created:

- a `DbtProject` object that points to the path of your dbt project
- a `DbtResource` that references the project object
- a `@dbt_assets` decorated function that yields Dagster events from the events streamed from the dbt CLI
- a `Definitions` object that contains your assets and resources

You also used `dbt_project.prepare_if_dev()` to compile the dbt project to ensure Dagster has what it needs to build the asset graph.

## Adding upstream dependencies
Oftentimes, you'll want Dagster to generate data that will be used by downstream dbt models. Next, you'll add an upstream asset to `definitions.py` that your dbt project will use as a source:

<CodeExample filePath="guides/etl/transform-dbt/dbt_definitions_with_upstream.py" language="python" title="Adding an upstream asset to definitions.py" />

This asset:

- Pulls customer data from a CSV with pandas
- Creates a schema called `raw` if it doesn't already exist
- Writes a `raw_customers` table to the `raw` schema in our DuckDB database
Next, you'll add a dbt model that will source that asset and define the dependency for Dagster. Create the dbt model first:

<CodeExample filePath="guides/etl/transform-dbt/basic-dbt-project/models/example/customers.sql" language="sql" title="customers.sql" />
Now you'll set up your `_source.yml` file that points dbt to the upstream asset:

<CodeExample filePath="guides/etl/transform-dbt/basic-dbt-project/models/example/_source.yml" language="yaml" title="Adding a _source.yml to our dbt project" />
In this file we need to add the Dagster metadata in the highlighted portion of the code to tell Dagster that this source data is coming from the `raw_customers` asset that we defined earlier. This file now serves two purposes:
1. It tells dbt where to find the source data for the `customers` model
2. It tells Dagster exactly which asset represents this source data

## Adding downstream dependencies
You may also have assets that depend on the output of dbt models. Next, create an asset that depends on the result of the new `customers` model. This asset will create a histogram of the first names of the customers:

<CodeExample filePath="guides/etl/transform-dbt/dbt_definitions_with_downstream.py" language="python" title="Adding an downstream asset to definitions.py" />
Take note of the following line, which is where you set the asset dependency to the customers model using the `get_asset_key_for_model` function:

```python
deps=get_asset_key_for_model([dbt_models], "customers")
```
This line finds our `customers` dbt model, gets its corresponding asset key, and directly sets it as a dependency of our new `customer_histogram` asset.

## Scheduling dbt models
You can schedule your dbt models by using the Dagster dbt integration's `build_schedule_from_dbt_selection` function:

<CodeExample filePath="guides/etl/transform-dbt/dbt_definitions_with_schedule.py" language="python" title="Scheduling our dbt models" />

## Next steps

[comment]: <> (TODO: Add link to dbt partitioning guide)