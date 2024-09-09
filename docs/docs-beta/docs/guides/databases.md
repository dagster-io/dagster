---
title: Connecting to databases
description: How to configure resources to connect to databases
sidebar_position: 10
---

In Dagster, *resources* are used to connect to databases by acting as a wrapper around database clients. The resource is registered along with connection details in the `Definitions` object, and can then be referenced from your asset definitions.

## What you'll learn

- How to connect to and query a local DuckDB database using the `DuckDBResource`
- How to connect to different databases in different environments, such as development and production.
- How to connect to a Snowflake database using the `SnowflakeResource`

<details>
  <summary>Prerequisites</summary>

To follow the steps in this guide, you'll need:

- Familiarity with [Asset definitions](/concepts/assets)

If you want to run the examples in this guide, you'll need:
- Connection information for a Snowflake database
- To `pip install` the `dagster-duckdb` and `dagster-snowflake` packages

</details>

## Define a DuckDB resource and use it in an asset definition

Here is an example of a DuckDB resource definition that's used to create two tables in the DuckDB database.

<CodeExample filePath="guides/external-systems/resource-duckdb-example.py" language="python" title="DuckDB Resource Example" />

## Define a resource that depends on an environment variable

Resources can be configured using environment variables to connect to environment-specific databases. For example, a resource can connect to a test database in a development environment and a live database in the production environment. You can change the resource definition in the previous example to use an `EnvVar` as shown here:

<CodeExample filePath="guides/external-systems/resource-duckdb-envvar-example.py" language="python" title="DuckDB Resource using EnvVar Example" />

When launching a run, the database path will be read from the `IRIS_DUCKDB_PATH` environment variable.

## Define a Snowflake resource and use it in an asset definition

Using the Snowflake resource is similar to using the DuckDB resource. Here is a complete example showing how to connect to a Snowflake database and create two tables:

<CodeExample filePath="guides/external-systems/resource-snowflake-example.py" language="python" title="Snowflake Resource Example" />

**Note:** before running this example, you will need to set the `SNOWFLAKE_PASSWORKD` environment variable.

## Other database resource types

See [Dagster Integrations](https://dagster.io/integrations) for resource types that connect to other databases. Some other popular resource types are:

* [`BigQueryResource`](https://dagster.io/integrations/dagster-gcp-bigquery)
* [`RedshiftClientResource`](https://dagster.io/integrations/dagster-aws-redshift)

## Next steps

- Explore how to use resources for [Connecting to APIs](/guides/apis)
- Go deeper into [Understanding Resources](/concepts/resources)

