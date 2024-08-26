---
title: Connecting to APIs
sidebar_position: 20
---

This guide describes how to connect to and interact with APIs in dagster.


## What you'll learn

- How to write a dagster Resource to connect to an API
- How to use that Resource in an asset

<details>
  <summary>Prerequisites</summary>

To follow the steps in this guide, you'll need:

- Familiarity with [Asset definitions](/concepts/assets)
- Familiarity with [Resources](/concepts/resources)
- Install the `requests` library: `pip install requests`

</details>

## Step 1: Write a Resource to connect to an API

Here is a minimal Resource for connecting to the an API that returns data about the sunrise and sunset times. In this example, the request URL has been hardcoded to query for data at San Francisco International Airport.

<CodeExample filePath="guides/external-systems/apis/minimal_resource.py" language="python" title="Simple Resource to connect to Sun API" />


## Step 2: Use the Resource in an asset

To use the Resource written in step 1, you can provide it to an asset like this:

<CodeExample filePath="guides/external-systems/apis/use_resource_in_asset.py" language="python" title="Use the XYZResource in an asset" />

## Next steps

- [Customize resources with configuration](/todo)
- Learn what [dagster-provided Resources](/todo) are available to use
