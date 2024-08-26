---
title: Connecting to APIs
sidebar_position: 20
---

This guide describes how to connect to and interact with APIs in dagster. In this guide you will use dagster Resources to connect to an external API. Using a Resource allows you to standardize how you connect to an external API across your project and use configuration to customize your connections.


## What you'll learn

- How to write a dagster Resource to connect to an API
- How to use that Resource in an asset
- How to configure a Resource
- How to source configuration values from environment variables

<details>
  <summary>Prerequisites</summary>

To follow the steps in this guide, you'll need:

- Familiarity with [Asset definitions](/concepts/assets)
- Familiarity with [Resources](/concepts/resources)
- Install the `requests` library: `pip install requests`

</details>

## Step 1: Write a Resource to connect to an API

Here is a minimal Resource for connecting to the an API that returns the sunrise time. In this example, the request URL has been hardcoded to query for data at San Francisco International Airport.

<CodeExample filePath="guides/external-systems/apis/minimal_resource.py" language="python" title="Resource to connect to Sun API" />


## Step 2: Use the Resource in an asset

To use the Resource written in Step 1, you can provide it to an asset like this:

<CodeExample filePath="guides/external-systems/apis/use_minimal_resource_in_asset.py" language="python" title="Use the SFOSunResource in an asset" />


## Step 3: Configure your Resource
Many APIs have configuration you can set to customize your usage. Here is an updated version of the Resource from Step 1 with configuration to allow for setting the query location:

<CodeExample filePath="guides/external-systems/apis/configurable_resource.py" language="python" title="Configurable Resource to connect to Sun API" />

## Step 4: Use the configurable Resource in an asset

The configurable Resource written in Step 3 can be provided to an asset exactly as before. When the Resource is initialized, you can pass values for each of the configuration options.

<CodeExample filePath="guides/external-systems/apis/use_configurable_resource_in_asset.py" language="python" title="Use the configurable SunResource in an asset" />

## Step 5: Sourcing configuration values from environment variables

You can configure your Resource using values that are stored in environment variables using the `EnvVar` class. In this example, there is a new `home_sunrise` asset. Rather than hardcoding the location of your home, you can set it in environment variables, and configure the `SunResource` by reading those values:

<CodeExample filePath="guides/external-systems/apis/env_var_configuration.py" language="python" title="Configure the Resource with values from environment variables" />


## Next steps

- [Authenticate to a resource](/guides/external-systems/authentication.md)
- [Use different Resources in different execution environments](/todo)
- Learn what [dagster-provided Resources](/todo) are available to use
