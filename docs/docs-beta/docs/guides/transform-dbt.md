---
title: Transforming data with dbt
sidebar_position: 20
sidebar_label: Transform data with dbt
last_update:
  date: 2024-08-26
  author: Nick Roach
---

Dagster orchestrates dbt alongside other technologies, so you can schedule dbt with Spark, Python, etc. in a single data pipeline. Dagster's asset-oriented approach allows Dagster to understand dbt at the level of individual dbt models.

<details>
  <summary>Prerequisites</summary>

To follow the steps in this guide, you'll need:

- A basic understanding of dbt, DuckDB, and Dagster concepts such as [assets](/todo) and [resources](/todo)
- To install the [dbt](https://docs.getdbt.com/docs/core/installation-overview) and [DuckDB CLIs](https://duckdb.org/docs/api/cli/overview.html)
- To install the following packages:

  ```shell
  pip install dagster duckdb plotly dagster-dbt dbt-duckdb
  ```
</details>

## Setting up a basic dbt project

Start by downloading this basic dbt project, which includes a few models and a DuckDB backend:

```bash
git clone https://github.com/dagster-io/basic-dbt-project
```

The project structure should look like this:

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

First, you need to point Dagster at the dbt project and ensure Dagster has what it needs to build an asset graph. Create a `definitions.py` in the same directory as the dbt project:

<CodeExample filePath="guides/etl/transform-dbt/dbt_definitions.py" language="python" title="definitions.py" />

## Adding upstream dependencies

Oftentimes, you'll want Dagster to generate data that will be used by downstream dbt models. To do this, add an upstream asset that the dbt project will as a source:

<CodeExample filePath="guides/etl/transform-dbt/dbt_definitions_with_upstream.py" language="python" title="definitions.py" />

Next, you'll add a dbt model that will source the `raw_customers` asset and define the dependency for Dagster. Create the dbt model:

<CodeExample filePath="guides/etl/transform-dbt/basic-dbt-project/models/example/customers.sql" language="sql" title="customers.sql" />

Next, create a `_source.yml` file that points dbt to the upstream `raw_customers` asset:

<CodeExample filePath="guides/etl/transform-dbt/basic-dbt-project/models/example/_source.yml" language="yaml" title="_source.yml_" />

![Screenshot of dbt lineage](/img/placeholder.svg)

## Adding downstream dependencies

You may also have assets that depend on the output of dbt models. Next, create an asset that depends on the result of the new `customers` model. This asset will create a histogram of the first names of the customers:

<CodeExample filePath="guides/etl/transform-dbt/dbt_definitions_with_downstream.py" language="python" title="definitions.py" />

## Scheduling dbt models

You can schedule your dbt models by using the `dagster-dbt`'s `build_schedule_from_dbt_selection` function:

<CodeExample filePath="guides/etl/transform-dbt/dbt_definitions_with_schedule.py" language="python" title="Scheduling our dbt models" />

## Next steps

{/* TODO: Add link to dbt partitioning guide */}
