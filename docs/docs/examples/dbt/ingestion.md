---
title: Ingestion
description: Load data into source tables
last_update:
  author: Dennis Hume
sidebar_position: 20
---

In order to work on a dbt project, we need both a storage layer and some data. While setting this up won’t be the focus of this example, it’s a necessary foundation for working effectively with dbt.

We’ll use DuckDB as our storage layer—a popular OLAP system known for its excellent performance on analytical queries and its ability to run locally. Our dbt project will rely on two tables in DuckDB:

* `taxi_trips`
* `taxi_zones`

The data for these tables resides in an S3 bucket. The first table, `taxi_zones`, is created directly from an S3 file using a CREATE TABLE query in DuckDB.

<CodeExample
  path="docs_projects/project_dbt/src/project_dbt/defs/assets/trips.py"
  language="python"
  startAfter="start_taxi_zones"
  endBefore="end_taxi_zones"
  title="src/project_dbt/defs/assets/trips.py"
/>

## Partitioned table

The second table, `taxi_trips`, is made up of multiple files spread across time. Each file represents a different month, making this a great use case for partitions, which allow us to organize the data chronologically.

This asset behaves similarly to `taxi_zones`, but with a key difference: instead of creating the table directly from an S3 file, we first create an empty table. Then, for each month, we `DELETE` the corresponding data before `INSERT` fresh data for that partition.

The partition key—used to determine which month of data to operate on—is provided via `context.partition_key`.

<CodeExample
  path="docs_projects/project_dbt/src/project_dbt/defs/assets/trips.py"
  language="python"
  startAfter="start_taxi_trips"
  endBefore="end_taxi_trips"
  title="src/project_dbt/defs/assets/trips.py"
/>

## More on ingestion

If you're interested in the ingestion layer—or if this setup looks familiar—much of it is borrowed from the [Dagster Essentials course](https://courses.dagster.io/courses/dagster-essentials), which covers asset creation and resource configuration in more detail.

But for now, with this foundation in place, we’re ready to start building with dbt in Dagster.

## Next steps

- Continue this example with [dbt project](/examples/dbt/dbt-project)
