---
title: Connecting to APIs
sidebar_position: 500
---

When building a data pipeline, you'll likely need to connect to several external APIs, each with its own specific configuration and behavior. This guide demonstrates how to standardize your API connections and customize their configuration using Dagster resources.

:::note

This guide assumes familiarity with [assets](/guides/build/assets/) and [resources](/guides/build/external-resources/).

:::

<details>
  <summary>Prerequisites</summary>

To run the example code in this article, you will need to install the `requests` library:
    ```bash
    pip install requests
    ```

</details>

## Step 1: Write a resource that connects to an API

This example fetches the sunrise time for a given location from a REST API.

Using `ConfigurableResource`, define a Dagster resource with a method that returns the sunrise time for a location. In the first version of this resource, the location is hard-coded to San Francisco International Airport.

<CodeExample path="docs_beta_snippets/docs_beta_snippets/guides/external-systems/apis/minimal_resource.py" language="python" />

## Step 2: Use the resource in an asset

To use the resource, provide it as a parameter to an asset and include it in the `Definitions` object:

<CodeExample path="docs_beta_snippets/docs_beta_snippets/guides/external-systems/apis/use_minimal_resource_in_asset.py" language="python" />

When you materialize `sfo_sunrise`, Dagster will provide an initialized `SunResource` to the `sun_resource` parameter.

## Step 3: Configure the resource

Many APIs have configuration you can set to customize your usage. The following example updates the resource with configuration to allow for setting the query location:

<CodeExample path="docs_beta_snippets/docs_beta_snippets/guides/external-systems/apis/use_configurable_resource_in_asset.py" language="python" />

The configurable resource can be provided to an asset exactly as before. When the resource is initialized, you can pass values for each of the configuration options.

When you materialize `sfo_sunrise`, Dagster will provide a `SunResource` initialized with the configuration values to the `sun_resource` parameter.

## Step 4: Source configuration using environment variables

Resources can also be configured with environment variables. You can use Dagster's built-in `EnvVar` class to source configuration values from environment variables at materialization time.

In this example, there's a new `home_sunrise` asset. Rather than hard-coding the location of your home, you can set it in environment variables and configure the `SunResource` by reading those values:

<CodeExample path="docs_beta_snippets/docs_beta_snippets/guides/external-systems/apis/env_var_configuration.py" language="python" />

When you materialize `home_sunrise`, Dagster will read the values set for the `HOME_LATITUDE`, `HOME_LONGITUDE`, and `HOME_TIMZONE` environment variables and initialize a `SunResource` with those values.

The initialized `SunResource` will be provided to the `sun_resource` parameter.

:::note
You can also fetch environment variables using the `os` library. Dagster treats each approach to fetching environment variables differently, such as when they're fetched or how they display in the UI. Refer to the [Environment variables guide](/guides/deploy/using-environment-variables-and-secrets) for more information.
:::

