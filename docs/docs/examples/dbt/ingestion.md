---
title: Ingestion
description: Load data into source tables
last_update:
  author: Dennis Hume
sidebar_position: 20
---

To work with dbt, you need both a storage layer and data. Setting these up isn’t the main focus here, but they’re the foundation for running dbt effectively.

We’ll use DuckDB as the storage layer. It’s a lightweight OLAP database that runs locally with minimal setup. Our dbt project will rely on two tables in DuckDB:

- `taxi_trips`
- `taxi_zones`

The data for these tables lives in cloud storage. The first table, `taxi_zones`, is created directly from an S3 file using [CREATE TABLE](https://duckdb.org/docs/stable/sql/statements/create_table.html):

<CodeExample
  path="docs_projects/project_dbt/src/project_dbt/defs/assets/trips.py"
  language="python"
  startAfter="start_taxi_zones"
  endBefore="end_taxi_zones"
  title="src/project_dbt/defs/assets/trips.py"
/>

## Partitioned table

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

## Resources

Since both assets use DuckDB, we need to configure a DuckDB resource in the Dagster project. This centralizes the connection and makes it reusable across Dagster entities:

<CodeExample
  path="docs_projects/project_dbt/src/project_dbt/defs/resources.py"
  language="python"
  title="src/project_dbt/defs/resources.py"
/>

A project can define multiple resources, but this is all we need for now.

## More on ingestion

This setup is based on the [Dagster Essentials course](https://courses.dagster.io/courses/dagster-essentials), which covers ingestion, asset creation, and resource configuration in more depth.

With this foundation in place, we’re ready to build with dbt in Dagster.

## Next steps

- Continue with the [dbt project](/examples/dbt/dbt-project)
