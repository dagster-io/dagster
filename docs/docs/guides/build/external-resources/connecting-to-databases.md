---
description: Standardize and configure database connections in Dagster using resources.
sidebar_position: 400
title: Connecting to databases
---

When building a data pipeline, you may need to extract data from or load data into a database. In Dagster, resources can be used to connect to a database by acting as a wrapper around a database client.

This guide demonstrates how to standardize database connections and customize their configuration using Dagster resources.

:::note

This guide assumes familiarity with [assets](/guides/build/assets).

:::

<details>
  <summary>Prerequisites</summary>

To run the example code in this article, you'll need:

- Connection information for a Snowflake database
- Install the necessary Python libraries:

<Tabs groupId="package-manager">
   <TabItem value="uv" label="uv">
      Install the required dependencies:

         ```shell
         uv add dagster-snowflake pandas
         ```

   </TabItem>

   <TabItem value="pip" label="pip">
      Install the required dependencies:

         ```shell
         pip install dagster-snowflake pandas
         ```

   </TabItem>
</Tabs>

</details>

## Step 1: Write a resource \{#step-one}

import ScaffoldResource from '@site/docs/partials/\_ScaffoldResource.md';

<ScaffoldResource />

This example creates a resource that represents a Snowflake database. Using `SnowflakeResource`, define a Dagster resource that connects to a Snowflake database:

<CodeExample path="docs_snippets/docs_snippets/guides/external-systems/databases/snowflake-resource.py" language="python" title="src/<project_name>/defs/resources.py" />

## Step 2: Use the resource in an asset \{#step-two}

import ScaffoldAsset from '@site/docs/partials/\_ScaffoldAsset.md';

<ScaffoldAsset />

To use the resource, provide it as a parameter to an asset and define a function using <PyObject section="definitions" module="dagster" object="Definitions" decorator />:

<CodeExample path="docs_snippets/docs_snippets/guides/external-systems/databases/use-in-asset.py" language="python" startAfter="start_use_in_asset" endBefore="end_use_in_asset" title="src/<project_name>/defs/assets.py" />

<CodeExample path="docs_snippets/docs_snippets/guides/external-systems/databases/use-in-asset.py" language="python" startAfter="start_use_in_asset_defs" endBefore="end_use_in_asset_defs" title="src/<project_name>/defs/resources.py" />

When you materialize these assets, Dagster will provide an initialized `SnowflakeResource` to the assets' `iris_db` parameter.

## Step 3: Source configuration with environment variables \{#step-three}

Resources can be configured using environment variables, allowing you to connect to environment-specific databases, swap credentials, and so on. You can use Dagster's built-in `EnvVar` class to source configuration values from environment variables at asset materialization time.

In this example, a second instance of the Snowflake resource, named `production` has been added:

<CodeExample path="docs_snippets/docs_snippets/guides/external-systems/databases/use-envvars.py" language="python" startAfter="start_use_envvars" endBefore="end_use_envvars" title="src/<project_name>/defs/assets.py" />

<CodeExample path="docs_snippets/docs_snippets/guides/external-systems/databases/use-envvars.py" language="python" startAfter="start_use_envvars_defs" endBefore="end_use_envvars_defs" title="src/<project_name>/defs/resources.py" />

When the assets are materialized, Dagster will use the `deployment_name` environment variable to determine which Snowflake resource to use (`local` or `production`). Then, Dagster will read the values set for each resource's environment variables (ex: `DEV_SNOWFLAKE_PASSWORD`) and initialize a `SnowflakeResource` with those values.

The initialized `SnowflakeResource` will be provided to the assets' `iris_db` parameter.

:::note
You can also fetch environment variables using the `os` library. Dagster treats each approach to fetching environment variables differently, such as when they're fetched or how they display in the UI. Refer to the [Environment variables guide](/guides/operate/configuration/using-environment-variables-and-secrets) for more information.
:::

## Next steps

- Explore how to use resources for [connecting to APIs](/guides/build/external-resources/connecting-to-apis)
- Go deeper into understanding [resources](/guides/build/external-resources)