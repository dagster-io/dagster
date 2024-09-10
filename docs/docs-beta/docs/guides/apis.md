---
title: Connecting to APIs
sidebar_position: 20
---

When building a data pipeline, you'll likely need to connect to several external APIs, each with its own specific configuration and behavior. This guide demonstrates how to standardize your API connections and customize their configuration using Dagster resources.


## What you'll learn

- How to connect to an API using a Dagster resource
- How to use that resource in an asset
- How to configure a resource
- How to source configuration values from environment variables

<details>
  <summary>Prerequisites</summary>

To follow the steps in this guide, you'll need:

- Familiarity with [Asset definitions](/concepts/assets)
- Familiarity with [resources](/concepts/resources)
- Install the `requests` library:
    ```bash
    pip install requests
    ```

</details>

## Step 1: Write a resource to connect to an API

This example fetches the sunrise time for a given location from a REST API.

Begin by defining a Dagster resource with a method to return the sunrise time for a location. In the first version of this resource, the location will be hard-coded to San Francisco International Airport.


<CodeExample filePath="guides/external-systems/apis/minimal_resource.py" language="python" title="Resource to connect to the Sunrise API" />


## Step 2: Use the resource in an asset

To use the resource written in Step 1, you can provide it as a parameter to an asset after including it in the Definitions object:

<CodeExample filePath="guides/external-systems/apis/use_minimal_resource_in_asset.py" language="python" title="Use the SunResource in an asset" />

When you materialize `sfo_sunrise`, Dagster will provide an initialized `SunResource` to the `sun_resource` parameter.


## Step 3: Configure your resource
Many APIs have configuration you can set to customize your usage. Here is an updated version of the resource from Step 1 with configuration to allow for setting the query location:

<CodeExample filePath="guides/external-systems/apis/use_configurable_resource_in_asset.py" language="python" title="Use the configurable SunResource in an asset" />

The configurable resource can be provided to an asset exactly as before. When the resource is initialized, you can pass values for each of the configuration options.

When you materialize `sfo_sunrise`, Dagster will provide a `SunResource` initialized with the configuration values to the `sun_resource` parameter.


## Step 4: Source configuration values from environment variables
Resources can also be configured with environment variables. You can use Dagster's built-in `EnvVar` class to source configuration values from environment variables at materialization time.

In this example, there is a new `home_sunrise` asset. Rather than hard-coding the location of your home, you can set it in environment variables, and configure the `SunResource` by reading those values:

<CodeExample filePath="guides/external-systems/apis/env_var_configuration.py" language="python" title="Configure the resource with values from environment variables" />

When you materialize `home_sunrise`, Dagster will read the values set for the `HOME_LATITUDE`, `HOME_LONGITUDE`, and `HOME_TIMZONE` environment variables and initialize a `SunResource` with those values.

The initialized `SunResource` will be provided to the `sun_resource` parameter.

:::note
You can also fetch environment variables using the `os` library. Dagster treats each approach to fetching environment variables differently, such as when they're fetched or how they display in the UI. Refer to the [Environment variables guide](/todo) for more information.
:::


## Next steps

- [Authenticate to a resource](/guides/authentication.md)
- [Use different resources in different execution environments](/todo)
- [Set environment variables in Dagster+](/todo)
- Learn what [Dagster-provided resources](/todo) are available to use
