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

Start by scaffolding a basic dbt project:

```bash
dbt init jaffle_shop
```

Make sure to select **DuckDB** as your database when prompted. This will create a dbt project with the following structure:

```
├── README.md
├── analyses
├── dbt_project.yml
├── logs
├── macros
├── models
│   └── example
│       ├── my_first_dbt_model.sql
│       ├── my_second_dbt_model.sql
│       └── schema.yml
├── seeds
├── snapshots
└── tests
```

If you try to build this example as is, it would immediately fail due to a non-null test not passing in `my_first_dbt_model.sql`. To fix this, you'll uncomment the last line in the model to filter out the null record:

<CodeExample filePath="guides/etl/transform-dbt/jaffle_shop/models/example/my_first_dbt_model.sql" language="sql" title="Fix my_first_dbt_model.sql failing test" />

Now Dagster has everything it needs to consume our dbt project and build our asset graph. Let's create a `definitions.py` file beside our dbt project:

<CodeExample filePath="guides/etl/transform-dbt/dbt_definitions.py" language="python" title="Importing a dbt project into Dagster" />

In this file you created:

- a `DbtProject` object that points to the path of your dbt project
- a `DbtResource` that references the project object
- a `@dbt_assets` decorated function that yields Dagster events from the events streamed from the dbt CLI
- a `Definitions` object that contains your assets and resources

You also used `dbt_project.prepare_if_dev()` to compile the dbt project to ensure Dagster has what it needs to build the asset graph.

## Adding upstream dependencies

Oftentimes, we want Dagster to generate data that will be used by downstream dbt models. Let's add an upstream asset to our `definitions.py` that our dbt project will use as a source:

<CodeExample filePath="guides/etl/transform-dbt/dbt_definitions_with_upstream.py" language="python" title="Adding an upstream asset to definitions.py" />

This asset:

- Pulls customer data from a CSV with pandas
- Creates a schema called `raw` if it doesn't already exist
- Writes a `raw_customers` table to the `raw` schema in our DuckDB database

Let's add a dbt model that will source that asset and define the dependency for Dagster, first we'll create our dbt model:

<CodeExample filePath="guides/etl/transform-dbt/jaffle_shop/models/example/customers.sql" language="sql" title="customers.sql" />

Now we'll set up our `_source.yml` file that will point dbt to our upstream asset:

<CodeExample filePath="guides/etl/transform-dbt/jaffle_shop/models/example/_source.yml" language="yaml" title="Adding a _source.yml to our dbt project" />

In this file we need to add the Dagster metadata in the highlighted portion of the code to tell Dagster that this source data is coming from the `raw_customers` asset that we defined earlier. This file now serves two purposes:

1. It's telling dbt where to find the source data for our `customers` model
2. It's telling Dagster exactly which asset represents this source data

## Adding downstream dependencies

Similarly, we often have assets that depend on the output of our dbt models. Let's create an asset that depends on the result of our new `customers` model, this asset will create a histogram of the first names of the customers:

<CodeExample filePath="guides/etl/transform-dbt/dbt_definitions_with_downstream.py" language="python" title="Adding an downstream asset to definitions.py" />

The important line to note is where we set the dependency of our asset to our customers model using the `get_asset_key_for_model` function:

```python
deps=get_asset_key_for_model([dbt_models], "customers")
```

This line finds our `customers` dbt model, gets its corresponding asset key, and directly sets it as a dependency of our new `customer_histogram` asset.

## Scheduling dbt models

We can easily schedule our dbt models using the Dagster dbt integration's `build_schedule_from_dbt_selection` function:

<CodeExample filePath="guides/etl/transform-dbt/dbt_definitions_with_schedule.py" language="python" title="Scheduling our dbt models" />

## Next steps

[comment]: <> (TODO: Add link to dbt partitioning guide)