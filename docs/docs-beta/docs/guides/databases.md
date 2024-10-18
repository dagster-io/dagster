---
title: Connecting to databases
description: How to configure resources to connect to databases
sidebar_position: 10
sidebar_label: Database connections
---

When building a data pipeline, you may need to extract data from or load data into a database. In Dagster, resources can be used to connect to a database by acting as a wrapper around a database client.

This guide demonstrates how to standardize database connections and customize their configuration using Dagster resources.

<details>
  <summary>Prerequisites</summary>

To follow the steps in this guide, you'll need:

- Familiarity with [Assets](/guides/data-assets)

To run the examples in this guide, you'll need:

- Connection information for a Snowflake database
- To install the following:

   ```bash
   pip install dagster dagster-snowflake pandas
   ```

</details>

## Step 1: Write a resource \{#step-one}

This example creates a resource that represents a Snowflake database. Using `SnowflakeResource`, define a Dagster resource that connects to a Snowflake database:

<CodeExample filePath="guides/external-systems/databases/snowflake-resource.py" language="python" />

## Step 2: Use the resource in an asset \{#step-two}

To use the resource, provide it as a parameter to an asset and include it in the `Definitions` object:

<CodeExample filePath="guides/external-systems/databases/use-in-asset.py" language="python" />

When you materialize these assets, Dagster will provide an initialized `SnowflakeResource` to the assets' `iris_db` parameter.

## Step 3: Source configuration with environment variables \{#step-three}

Resources can be configured using environment variables, allowing you to connect to environment-specific databases, swap credentials, and so on. You can use Dagster's built-in `EnvVar` class to source configuration values from environment variables at asset materialization time.

In this example, a second instance of the Snowflake resource, named `production` has been added:

<CodeExample filePath="guides/external-systems/databases/use-envvars.py" language="python" />

When the assets are materialized, Dagster will use the `deployment_name` environment variable to determine which Snowflake resource to use (`local` or `production`). Then, Dagster will read the values set for each resource's environment variables (ex: `DEV_SNOWFLAKE_PASSWORD`) and initialize a `SnowflakeResource` with those values.

The initialized `SnowflakeResource` will be provided to the assets' `iris_db` parameter.

:::note
You can also fetch environment variables using the `os` library. Dagster treats each approach to fetching environment variables differently, such as when they're fetched or how they display in the UI. Refer to the [Environment variables guide](/todo) for more information.
:::

## Next steps

- Explore how to use resources for [Connecting to APIs](/guides/apis)
- Go deeper into [Understanding Resources](/concepts/resources)