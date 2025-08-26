---
title: Ingestion
description: Load data into source tables
last_update:
  author: Dennis Hume
sidebar_position: 20
---

In order to work on a dbt project, we need both a storage layer and data. While setting this up won’t be the focus of this example, it’s a necessary foundation for working effectively with dbt.

We’ll use DuckDB as our storage layer since it is a OLAP database we can run locally with minimal setup. Our dbt project will rely on two tables in DuckDB:

- `taxi_trips`
- `taxi_zones`

The data for these tables resides in cloud storage. The first table, `taxi_zones`, is created directly from an S3 file using [CREATE TABLE](https://duckdb.org/docs/stable/sql/statements/create_table.html):

<CodeExample
  path="docs_projects/project_dbt/src/project_dbt/defs/assets/trips.py"
  language="python"
  startAfter="start_taxi_zones"
  endBefore="end_taxi_zones"
  title="src/project_dbt/defs/assets/trips.py"
/>

## Partitioned table

The second table, `taxi_trips`, is made up of multiple files spread across time. Each file represents a different month, making this a great use case for [partitions](/guides/build/partitions-and-backfills), which allow us to organize the underlying data into separate chronological sections.

Similar to the `taxi_zones` data, all of the files are in cloud storage. But the asset for `taxi_trips` will look slightly different because instead of creating the table directly from an S3 file, we will first create an empty table and then populate it for each month according to each partition. When we execute the asset for a specific partition, data will be removed from the table with `DELETE` before that month's data is added with an `INSERT`. This ensures that our asset remains idempotent:

<CodeExample
  path="docs_projects/project_dbt/src/project_dbt/defs/assets/trips.py"
  language="python"
  startAfter="start_taxi_trips"
  endBefore="end_taxi_trips"
  title="src/project_dbt/defs/assets/trips.py"
/>

The partition key used to determine the month of data to operate on—is provided via `context.partition_key`.

## Resources

Since both of our assets rely on DuckDB, we will need to configure a DuckDB resource in the Dagster project. This standardize and share the connection across any Dagster entities that use the resource:

<CodeExample
  path="docs_projects/project_dbt/src/project_dbt/defs/resources.py"
  language="python"
  title="src/project_dbt/defs/resources.py"
/>

Dagster projects can have any number of resources, but this is all that is needed for this example.

## More on ingestion

If you're interested in the ingestion layer or if this setup looks familiar, much of it is borrowed from the [Dagster Essentials course](https://courses.dagster.io/courses/dagster-essentials). This course covers asset creation and resource configuration in much more detail.

But for now, with this foundation in place, we’re ready to start building with dbt in Dagster.

## Next steps

- Continue this example with [dbt project](/examples/dbt/dbt-project)
