---
layout: Integration
status: published
name: Airbyte Cloud
title: Using Dagster with Airbyte Cloud
sidebar_label: Airbyte Cloud
excerpt: Orchestrate Airbyte Cloud connections and schedule syncs alongside upstream or downstream dependencies.
date: 2022-11-07
apireflink: https://docs.dagster.io/_apidocs/libraries/dagster-airbyte
docslink: https://docs.dagster.io/integrations/airbyte-cloud
partnerlink: https://airbyte.com/tutorials/orchestrate-data-ingestion-and-transformation-pipelines
logo: /integrations/airbyte.svg
categories:
  - ETL
enabledBy:
enables:
tags: [dagster-supported, etl]
sidebar_custom_props: 
  logo: images/integrations/airbyte.svg
---

This guide provides instructions for using Dagster with Airbyte Cloud using the `dagster-airbyte` library. Your Airbyte Cloud connection tables can be represented as assets in the Dagster asset graph, allowing you to track lineage and dependencies between Airbyte Cloud assets and data assets you are already modeling in Dagster. You can also use Dagster to orchestrate Airbyte Cloud connections, allowing you to trigger syncs for these on a cadence or based on upstream data changes.

## What you'll learn

- How to represent Airbyte Cloud assets in the Dagster asset graph, including lineage to other Dagster assets.
- How to customize asset definition metadata for these Airbyte Cloud assets.
- How to materialize Airbyte Cloud connection tables from Dagster.
- How to customize how Airbyte Cloud connection tables are materialized.

<details>
  <summary>Prerequisites</summary>

- The `dagster` and `dagster-airbyte` libraries installed in your environment
- Familiarity with asset definitions and the Dagster asset graph
- Familiarity with Dagster resources
- Familiarity with Airbyte Cloud concepts, like connections and connection tables
- An Airbyte Cloud workspace
- An Airbyte Cloud client ID and client secret. For more information, see [Configuring API Access](https://docs.airbyte.com/using-airbyte/configuring-api-access) in the Airbyte Cloud REST API documentation.

</details>

## Set up your environment

To get started, you'll need to install the `dagster` and `dagster-airbyte` Python packages:

```bash
pip install dagster dagster-airbyte
```

## Represent Airbyte Cloud assets in the asset graph

To load Airbyte Cloud assets into the Dagster asset graph, you must first construct a <PyObject section="libraries" module="dagster_airbyte" object="AirbyteCloudWorkspace" /> resource, which allows Dagster to communicate with your Airbyte Cloud workspace. You'll need to supply your workspace ID, client ID and client secret. See [Configuring API Access](https://docs.airbyte.com/using-airbyte/configuring-api-access) in the Airbyte Cloud REST API documentation for more information on how to create your client ID and client secret.

Dagster can automatically load all connection tables from your Airbyte Cloud workspace as asset specs. Call the <PyObject section="libraries" module="dagster_airbyte" object="load_airbyte_cloud_asset_specs" /> function, which returns list of <PyObject section="assets" object="AssetSpec" />s representing your Airbyte Cloud assets. You can then include these asset specs in your <PyObject section="definitions" module="dagster" object="Definitions" /> object:

<CodeExample filePath="integrations/airbyte_cloud/representing_airbyte_cloud_assets.py" language="python" />

### Sync and materialize Airbyte Cloud assets

You can use Dagster to sync Airbyte Cloud connections and materialize Airbyte Cloud connection tables. You can use the <PyObject section="libraries" module="dagster_airbyte" object="build_airbyte_assets_definitions" /> factory to create all assets definitions for your Airbyte Cloud workspace.

<CodeExample filePath="integrations/airbyte_cloud/sync_and_materialize_airbyte_cloud_assets.py" language="python" />

### Customize the materialization of Airbyte Cloud assets

If you want to customize the sync of your connections, you can use the <PyObject section="libraries" module="dagster_airbyte" object="airbyte_assets" /> decorator to do so. This allows you to execute custom code before and after the call to the Airbyte Cloud sync.

<CodeExample filePath="integrations/airbyte_cloud/customize_airbyte_cloud_asset_defs.py" language="python" />

### Customize asset definition metadata for Airbyte Cloud assets

By default, Dagster will generate asset specs for each Airbyte Cloud asset and populate default metadata. You can further customize asset properties by passing an instance of the custom <PyObject section="libraries" module="dagster_airbyte" object="DagsterAirbyteTranslator" /> to the <PyObject section="libraries" module="dagster_airbyte" object="load_airbyte_cloud_asset_specs" /> function.

<CodeExample filePath="integrations/airbyte_cloud/customize_airbyte_cloud_translator_asset_spec.py" language="python" />

Note that `super()` is called in each of the overridden methods to generate the default asset spec. It is best practice to generate the default asset spec before customizing it.

You can pass an instance of the custom <PyObject section="libraries" module="dagster_airbyte" object="DagsterAirbyteTranslator" /> to the <PyObject section="libraries" module="dagster_airbyte" object="airbyte_assets" /> decorator or the <PyObject section="libraries" module="dagster_airbyte" object="build_airbyte_assets_definitions" /> factory.

### Load Airbyte Cloud assets from multiple workspaces

Definitions from multiple Airbyte Cloud workspaces can be combined by instantiating multiple <PyObject section="libraries" module="dagster_airbyte" object="AirbyteCloudWorkspace" /> resources and merging their specs. This lets you view all your Airbyte Cloud assets in a single asset graph:

<CodeExample filePath="integrations/airbyte_cloud/multiple_airbyte_cloud_workspaces.py" language="python" />
