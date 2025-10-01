---
title: Set up data ingestion
description: Load data into DuckDB source tables
last_update:
  author: Dennis Hume
sidebar_position: 20
---

To work with dbt, you need both a storage layer and data. Setting these up isn’t the main focus of this example, but they’re the foundation for running dbt effectively.

We’ll use [DuckDB](https://duckdb.org/) as the storage layer for this example. DuckDB is a lightweight OLAP database that runs locally with minimal setup. Our dbt project will rely on two tables in DuckDB:

- `taxi_zones`
- `taxi_trips`

## 1. Create `taxi_zones` table

The first table, `taxi_zones`, is created directly from an S3 file using [CREATE TABLE](https://duckdb.org/docs/stable/sql/statements/create_table.html):

<CodeExample
  path="docs_projects/project_dbt/src/project_dbt/defs/assets/trips.py"
  language="python"
  startAfter="start_taxi_zones"
  endBefore="end_taxi_zones"
  title="src/project_dbt/defs/assets/trips.py"
/>

## 2. Create partitioned `taxi_trips` table

The second table, `taxi_trips`, comes from multiple monthly files. Each file represents a month of data, making this a natural use case for [partitions](/guides/build/partitions-and-backfills), which split data into chronological sections.

Like `taxi_zones`, the files are in cloud storage. But instead of creating the table directly from a file, we first create an empty table and then populate it per month. When you run the asset for a partition, it deletes that month’s data with `DELETE` and reloads it with `INSERT`. This keeps the asset idempotent:

<CodeExample
  path="docs_projects/project_dbt/src/project_dbt/defs/assets/trips.py"
  language="python"
  startAfter="start_taxi_trips"
  endBefore="end_taxi_trips"
  title="src/project_dbt/defs/assets/trips.py"
/>

The partition key that selects the month is available in `context.partition_key`.

## 3. Configure a DuckDB resource

Since both assets use DuckDB, we need to configure a DuckDB [resource](/guides/build/external-resources) in the Dagster project. This centralizes the connection and makes it reusable across Dagster entities:

<CodeExample
  path="docs_projects/project_dbt/src/project_dbt/defs/resources.py"
  language="python"
  title="src/project_dbt/defs/resources.py"
/>

A project can define multiple resources, but this is all we need for now. With this foundation in place, we’re ready to build with dbt in Dagster.

:::tip

This setup is based on the [Dagster Essentials course](https://courses.dagster.io/courses/dagster-essentials), which covers ingestion, asset creation, and resource configuration in more depth.

:::

## Next steps

- Continue with the [dbt project](/examples/full-pipelines/dbt/dbt-project).
