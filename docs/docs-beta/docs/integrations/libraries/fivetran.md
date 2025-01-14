---
layout: Integration
status: published
name: Fivetran
title: Using Dagster with Fivetran
sidebar_label: Fivetran
excerpt: Orchestrate Fivetran connectors syncs with upstream or downstream dependencies.
date: 2022-11-07
apireflink: https://docs.dagster.io/_apidocs/libraries/dagster-fivetran
docslink: https://docs.dagster.io/integrations/fivetran
partnerlink: https://www.fivetran.com/
logo: /integrations/Fivetran.svg
categories:
  - ETL
enabledBy:
enables:
tags: [dagster-supported, etl]
sidebar_custom_props: 
  logo: images/integrations/fivetran.svg
---

This guide provides instructions for using Dagster with Fivetran using the `dagster-fivetran` library. Your Fivetran connector tables can be represented as assets in the Dagster asset graph, allowing you to track lineage and dependencies between Fivetran assets and data assets you are already modeling in Dagster. You can also use Dagster to orchestrate Fivetran connectors, allowing you to trigger syncs for these on a cadence or based on upstream data changes.

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

```bash
pip install dagster dagster-fivetran
```

## Represent Fivetran assets in the asset graph

To load Fivetran assets into the Dagster asset graph, you must first construct a <PyObject section="libraries" module="dagster_fivetran" object="FivetranWorkspace" /> resource, which allows Dagster to communicate with your Fivetran workspace. You'll need to supply your account ID, API key and API secret. See [Getting Started](https://fivetran.com/docs/rest-api/getting-started) in the Fivetran REST API documentation for more information on how to create your API key and API secret.

Dagster can automatically load all connector tables from your Fivetran workspace as asset specs. Call the <PyObject section="libraries" module="dagster_fivetran" object="load_fivetran_asset_specs" /> function, which returns list of <PyObject section="assets" module="dagster" object="AssetSpec" />s representing your Fivetran assets. You can then include these asset specs in your <PyObject section="definitions" module="dagster" object="Definitions" /> object:

<CodeExample filePath="integrations/fivetran/representing_fivetran_assets.py" language="python" />

### Sync and materialize Fivetran assets

You can use Dagster to sync Fivetran connectors and materialize Fivetran connector tables. You can use the <PyObject section="libraries" module="dagster_fivetran" object="build_fivetran_assets_definitions" /> factory to create all assets definitions for your Fivetran workspace.

<CodeExample filePath="integrations/fivetran/sync_and_materialize_fivetran_assets.py" language="python" />

### Customize the materialization of Fivetran assets

If you want to customize the sync of your connectors, you can use the <PyObject section="libraries" module="dagster_fivetran" object="fivetran_assets" /> decorator to do so. This allows you to execute custom code before and after the call to the Fivetran sync.

<CodeExample filePath="integrations/fivetran/customize_fivetran_asset_defs.py" language="python" />

### Customize asset definition metadata for Fivetran assets

By default, Dagster will generate asset specs for each Fivetran asset and populate default metadata. You can further customize asset properties by passing an instance of the custom <PyObject section="libraries" module="dagster_fivetran" object="DagsterFivetranTranslator" /> to the <PyObject section="libraries" module="dagster_fivetran" object="load_fivetran_asset_specs" /> function.

<CodeExample filePath="integrations/fivetran/customize_fivetran_translator_asset_spec.py" language="python" />

Note that `super()` is called in each of the overridden methods to generate the default asset spec. It is best practice to generate the default asset spec before customizing it.

You can pass an instance of the custom <PyObject section="libraries" module="dagster_fivetran" object="DagsterFivetranTranslator" /> to the <PyObject section="libraries" module="dagster_fivetran" object="fivetran_assets" /> decorator or the <PyObject section="libraries" module="dagster_fivetran" object="build_fivetran_assets_definitions" /> factory.

### Fetching column-level metadata for Fivetran assets

Dagster allows you to emit column-level metadata, like [column schema](/guides/build/assets/organizing-assets-with-tags-and-metadata#standard-metadata-types) and [column lineage](/guides/build/assets/organizing-assets-with-tags-and-metadata#column-lineage), as [materialization metadata](/guides/build/assets/organizing-assets-with-tags-and-metadata#runtime-metadata).

With this metadata, you can view documentation in Dagster for all columns in your Fivetran connector tables.

To enable this feature, call <PyObject section="libraries" object="fivetran_event_iterator.FivetranEventIterator.fetch_column_metadata" module="dagster_fivetran" displayText="fetch_column_metadata()" /> on the <PyObject section="libraries" object="fivetran_event_iterator.FivetranEventIterator" module="dagster_fivetran" /> returned by the `sync_and_poll()` call on the <PyObject section="libraries" module="dagster_fivetran" object="FivetranWorkspace" /> resource.

<CodeExample filePath="integrations/fivetran/fetch_column_metadata_fivetran_assets.py" language="python" />

### Load Fivetran assets from multiple workspaces

Definitions from multiple Fivetran workspaces can be combined by instantiating multiple <PyObject section="libraries" module="dagster_fivetran" object="FivetranWorkspace" /> resources and merging their specs. This lets you view all your Fivetran assets in a single asset graph:

<CodeExample filePath="integrations/fivetran/multiple_fivetran_workspaces.py" language="python" />

### About Fivetran

**Fivetran** ingests data from SaaS applications, databases, and servers. The data is stored and typically used for analytics.
