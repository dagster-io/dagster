---
title: Using Dagster with Fivetran
sidebar_label: Fivetran
description: Orchestrate Fivetran connectors syncs with upstream or downstream dependencies.
tags: [dagster-supported, etl]
source: https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-fivetran
pypi: https://pypi.org/project/dagster-fivetran/
sidebar_custom_props:
  logo: images/integrations/fivetran.svg
partnerlink: https://www.fivetran.com/
---

This guide provides instructions for using Dagster with Fivetran using the `dagster-fivetran` library. Your Fivetran connector tables can be represented as assets in the Dagster asset graph, allowing you to track lineage and dependencies between Fivetran assets and data assets you are already modeling in Dagster. You can also use Dagster to orchestrate Fivetran connectors, allowing you to trigger syncs for these on a cadence or based on upstream data changes.

:::note

Your Fivetran connectors must have been synced at least once to be represented in Dagster.

:::

## What you'll learn

- How to represent Fivetran assets in the Dagster asset graph, including lineage to other Dagster assets.
- How to customize asset definition metadata for these Fivetran assets.
- How to materialize Fivetran connector tables from Dagster.
- How to customize how Fivetran connector tables are materialized.

<details>
  <summary>Prerequisites</summary>

- The `dagster` and `dagster-fivetran` libraries installed in your environment
- Familiarity with asset definitions and the Dagster asset graph
- Familiarity with Dagster resources
- Familiarity with Fivetran concepts, like connectors and connector tables
- A Fivetran workspace
- A Fivetran API key and API secret. For more information, see [Getting Started](https://fivetran.com/docs/rest-api/getting-started) in the Fivetran REST API documentation.

</details>

## Set up your environment

To get started, you'll need to install the `dagster` and `dagster-fivetran` Python packages:

<PackageInstallInstructions packageName="dagster-fivetran" />

## Represent Fivetran assets in the asset graph

To load Fivetran assets into the Dagster asset graph, you must first construct a <PyObject section="libraries" module="dagster_fivetran" object="FivetranWorkspace" /> resource, which allows Dagster to communicate with your Fivetran workspace. You'll need to supply your account ID, API key and API secret. See [Getting Started](https://fivetran.com/docs/rest-api/getting-started) in the Fivetran REST API documentation for more information on how to create your API key and API secret.

Dagster can automatically load all connector tables from your Fivetran workspace as asset specs. Call the <PyObject section="libraries" module="dagster_fivetran" object="load_fivetran_asset_specs" /> function, which returns list of <PyObject section="assets" module="dagster" object="AssetSpec" />s representing your Fivetran assets. You can then include these asset specs in your <PyObject section="definitions" module="dagster" object="Definitions" /> object:

<CodeExample
  path="docs_snippets/docs_snippets/integrations/fivetran/representing_fivetran_assets.py"
  language="python"
/>

### Sync and materialize Fivetran assets

You can use Dagster to sync Fivetran connectors and materialize Fivetran connector tables. You can use the <PyObject section="libraries" module="dagster_fivetran" object="build_fivetran_assets_definitions" /> factory to create all assets definitions for your Fivetran workspace.

<CodeExample
  path="docs_snippets/docs_snippets/integrations/fivetran/sync_and_materialize_fivetran_assets.py"
  language="python"
/>

### Customize the materialization of Fivetran assets

If you want to customize the sync of your connectors, you can use the <PyObject section="libraries" module="dagster_fivetran" object="fivetran_assets" /> decorator to do so. This allows you to execute custom code before and after the call to the Fivetran sync.

<CodeExample
  path="docs_snippets/docs_snippets/integrations/fivetran/customize_fivetran_asset_defs.py"
  language="python"
/>

### Customize asset definition metadata for Fivetran assets

By default, Dagster will generate asset specs for each Fivetran asset and populate default metadata. You can further customize asset properties by passing an instance of the custom <PyObject section="libraries" module="dagster_fivetran" object="DagsterFivetranTranslator" /> to the <PyObject section="libraries" module="dagster_fivetran" object="load_fivetran_asset_specs" /> function.

<CodeExample
  path="docs_snippets/docs_snippets/integrations/fivetran/customize_fivetran_translator_asset_spec.py"
  language="python"
/>

Note that `super()` is called in each of the overridden methods to generate the default asset spec. It is best practice to generate the default asset spec before customizing it.

You can pass an instance of the custom <PyObject section="libraries" module="dagster_fivetran" object="DagsterFivetranTranslator" /> to the <PyObject section="libraries" module="dagster_fivetran" object="fivetran_assets" /> decorator or the <PyObject section="libraries" module="dagster_fivetran" object="build_fivetran_assets_definitions" /> factory.

### Fetching column-level metadata for Fivetran assets

Dagster allows you to emit column-level metadata, like [column schema](/guides/build/assets/metadata-and-tags/index.md#standard-metadata-types) and [column lineage](/guides/build/assets/metadata-and-tags/index.md#column-lineage), as [materialization metadata](/guides/build/assets/metadata-and-tags/index.md#runtime-metadata).

With this metadata, you can view documentation in Dagster for all columns in your Fivetran connector tables.

To enable this feature, call <PyObject section="libraries" object="fivetran_event_iterator.FivetranEventIterator.fetch_column_metadata" module="dagster_fivetran" displayText="fetch_column_metadata()" /> on the <PyObject section="libraries" object="fivetran_event_iterator.FivetranEventIterator" module="dagster_fivetran" /> returned by the `sync_and_poll()` call on the <PyObject section="libraries" module="dagster_fivetran" object="FivetranWorkspace" /> resource.

<CodeExample
  path="docs_snippets/docs_snippets/integrations/fivetran/fetch_column_metadata_fivetran_assets.py"
  language="python"
/>

### Load Fivetran asset for selected connectors

To select a subset of Fivetran connectors for which your Fivetran assets will be loaded, you can use the <PyObject section="libraries" module="dagster_fivetran" object="ConnectorSelectorFn" /> callback and define your selection conditions.

<CodeExample path="docs_snippets/docs_snippets/integrations/fivetran/select_fivetran_connectors.py" language="python" />

### Load Fivetran assets from multiple workspaces

Definitions from multiple Fivetran workspaces can be combined by instantiating multiple <PyObject section="libraries" module="dagster_fivetran" object="FivetranWorkspace" /> resources and merging their specs. This lets you view all your Fivetran assets in a single asset graph:

<CodeExample
  path="docs_snippets/docs_snippets/integrations/fivetran/multiple_fivetran_workspaces.py"
  language="python"
/>

### Define upstream dependencies

By default, Dagster does not set upstream dependencies when generating asset specs for your Fivetran assets. You can set upstream dependencies on your Fivetran assets by passing an instance of the custom <PyObject section="libraries" module="dagster_fivetran" object="DagsterFivetranTranslator" /> to the <PyObject section="libraries" module="dagster_fivetran" object="load_fivetran_asset_specs" /> function.

<CodeExample
  startAfter="start_upstream_asset"
  endBefore="end_upstream_asset"
  path="docs_snippets/docs_snippets/integrations/fivetran/define_upstream_dependencies.py"
/>

Note that `super()` is called in each of the overridden methods to generate the default asset spec. It is best practice to generate the default asset spec before customizing it.

You can pass an instance of the custom <PyObject section="libraries" module="dagster_fivetran" object="DagsterFivetranTranslator" /> to the <PyObject section="libraries" module="dagster_fivetran" object="fivetran_assets" /> decorator or the <PyObject section="libraries" module="dagster_fivetran" object="build_fivetran_assets_definitions" /> factory.

### Define downstream dependencies

Dagster allows you to define assets that are downstream of specific Fivetran tables using their asset keys. The asset key for a Fivetran table can be retrieved using the asset definitions created using the <PyObject section="libraries" module="dagster_fivetran" object="fivetran_assets" /> decorator. The below example defines `my_downstream_asset` as a downstream dependency of `my_fivetran_table`:

<CodeExample
  startAfter="start_downstream_asset"
  endBefore="end_downstream_asset"
  path="docs_snippets/docs_snippets/integrations/fivetran/define_downstream_dependencies.py"
/>

In the downstream asset, you may want direct access to the contents of the Fivetran table. To do so, you can customize the code within your `@asset`-decorated function to load upstream data.

### About Fivetran

**Fivetran** ingests data from SaaS applications, databases, and servers. The data is stored and typically used for analytics.
