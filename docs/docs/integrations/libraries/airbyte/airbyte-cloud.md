---
title: Using Dagster with Airbyte Cloud
sidebar_label: Airbyte Cloud
description: Orchestrate Airbyte Cloud connections and schedule syncs alongside upstream or downstream dependencies.
tags: [dagster-supported, etl]
source: https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-airbyte
pypi: https://pypi.org/project/dagster-airbyte/
sidebar_custom_props:
  logo: images/integrations/airbyte.svg
partnerlink: https://airbyte.com/tutorials/orchestrate-data-ingestion-and-transformation-pipelines
---

import Beta from '@site/docs/partials/\_Beta.md';

<Beta />

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

<PackageInstallInstructions packageName="dagster-airbyte" />

## Represent Airbyte Cloud assets in the asset graph

To load Airbyte Cloud assets into the Dagster asset graph, you must first construct a <PyObject section="libraries" module="dagster_airbyte" object="AirbyteCloudWorkspace" /> resource, which allows Dagster to communicate with your Airbyte Cloud workspace. You'll need to supply your workspace ID, client ID and client secret. See [Configuring API Access](https://docs.airbyte.com/using-airbyte/configuring-api-access) in the Airbyte Cloud REST API documentation for more information on how to create your client ID and client secret.

Dagster can automatically load all connection tables from your Airbyte Cloud workspace as asset specs. Call the <PyObject section="libraries" module="dagster_airbyte" object="load_airbyte_cloud_asset_specs" /> function, which returns list of <PyObject section="assets" object="AssetSpec" />s representing your Airbyte Cloud assets. You can then include these asset specs in your <PyObject section="definitions" module="dagster" object="Definitions" /> object:

<CodeExample
  path="docs_snippets/docs_snippets/integrations/airbyte_cloud/representing_airbyte_cloud_assets.py"
  language="python"
/>

### Sync and materialize Airbyte Cloud assets

You can use Dagster to sync Airbyte Cloud connections and materialize Airbyte Cloud connection tables. You can use the <PyObject section="libraries" module="dagster_airbyte" object="build_airbyte_assets_definitions" /> factory to create all assets definitions for your Airbyte Cloud workspace.

<CodeExample
  path="docs_snippets/docs_snippets/integrations/airbyte_cloud/sync_and_materialize_airbyte_cloud_assets.py"
  language="python"
/>

### Customize the materialization of Airbyte Cloud assets

If you want to customize the sync of your connections, you can use the <PyObject section="libraries" module="dagster_airbyte" object="airbyte_assets" /> decorator to do so. This allows you to execute custom code before and after the call to the Airbyte Cloud sync.

<CodeExample
  path="docs_snippets/docs_snippets/integrations/airbyte_cloud/customize_airbyte_cloud_asset_defs.py"
  language="python"
/>

### Customize asset definition metadata for Airbyte Cloud assets

By default, Dagster will generate asset specs for each Airbyte Cloud asset and populate default metadata. You can further customize asset properties by passing an instance of the custom <PyObject section="libraries" module="dagster_airbyte" object="DagsterAirbyteTranslator" /> to the <PyObject section="libraries" module="dagster_airbyte" object="load_airbyte_cloud_asset_specs" /> function.

<CodeExample
  path="docs_snippets/docs_snippets/integrations/airbyte_cloud/customize_airbyte_cloud_translator_asset_spec.py"
  language="python"
/>

Note that `super()` is called in each of the overridden methods to generate the default asset spec. It is best practice to generate the default asset spec before customizing it.

You can pass an instance of the custom <PyObject section="libraries" module="dagster_airbyte" object="DagsterAirbyteTranslator" /> to the <PyObject section="libraries" module="dagster_airbyte" object="airbyte_assets" /> decorator or the <PyObject section="libraries" module="dagster_airbyte" object="build_airbyte_assets_definitions" /> factory.

### Load Airbyte Cloud assets from multiple workspaces

Definitions from multiple Airbyte Cloud workspaces can be combined by instantiating multiple <PyObject section="libraries" module="dagster_airbyte" object="AirbyteCloudWorkspace" /> resources and merging their specs. This lets you view all your Airbyte Cloud assets in a single asset graph:

<CodeExample
  path="docs_snippets/docs_snippets/integrations/airbyte_cloud/multiple_airbyte_cloud_workspaces.py"
  language="python"
/>

### Define upstream dependencies

By default, Dagster does not set upstream dependencies when generating asset specs for your Airbyte Cloud assets. You can set upstream dependencies on your Airbyte Cloud assets by passing an instance of the custom <PyObject section="libraries" module="dagster_airbyte" object="DagsterAirbyteTranslator" /> to the <PyObject section="libraries" module="dagster_airbyte" object="load_airbyte_cloud_asset_specs" /> function.

<CodeExample
  startAfter="start_upstream_asset"
  endBefore="end_upstream_asset"
  path="docs_snippets/docs_snippets/integrations/airbyte_cloud/define_upstream_dependencies.py"
/>

Note that `super()` is called in each of the overridden methods to generate the default asset spec. It is best practice to generate the default asset spec before customizing it.

You can pass an instance of the custom <PyObject section="libraries" module="dagster_airbyte" object="DagsterAirbyteTranslator" /> to the <PyObject section="libraries" module="dagster_airbyte" object="airbyte_assets" /> decorator or the <PyObject section="libraries" module="dagster_airbyte" object="build_airbyte_assets_definitions" /> factory.

### Define downstream dependencies

Dagster allows you to define assets that are downstream of specific Airbyte Cloud tables using their asset keys. The asset key for an Airbyte Cloud table can be retrieved using the asset definitions created using the <PyObject section="libraries" module="dagster_airbyte" object="airbyte_assets" /> decorator. The below example defines `my_downstream_asset` as a downstream dependency of `my_airbyte_cloud_table`:

<CodeExample
  startAfter="start_downstream_asset"
  endBefore="end_downstream_asset"
  path="docs_snippets/docs_snippets/integrations/airbyte_cloud/define_downstream_dependencies.py"
/>

In the downstream asset, you may want direct access to the contents of the Airbyte Cloud table. To do so, you can customize the code within your `@asset`-decorated function to load upstream data.
