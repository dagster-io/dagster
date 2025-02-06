---
title: "Using Looker with Dagster"
description: Represent your Looker assets in Dagster
---

:::

This feature is considered **experimental**

:::


This guide provides instructions for using Dagster with Looker using the `dagster-looker` library. Your Looker assets, such as views, explores, and dashboards, can be represented in the Dagster asset graph, allowing you to track lineage and dependencies between Looker assets. You can also use Dagster to orchestrate Looker PDTs, allowing you to trigger refreshes of these materialized tables on a cadence or based on upstream data changes.

## What you'll learn

- How to represent Looker assets in the Dagster asset graph.
- How to customize asset definition metadata for these Looker assets.
- How to materialize Looker PDTs from Dagster.

<details>
  <summary>Prerequisites</summary>

- The `dagster-looker` library installed in your environment
- Familiarity with asset definitions and the Dagster asset graph
- Familiarity with Dagster resources
- Familiarity with Looker concepts, like views, explores, and dashboards
- A Looker instance
- Looker API credentials to access your Looker instance. For more information, see [Looker API authentication](https://cloud.google.com/looker/docs/api-auth) in the Looker documentation.

</details>

## Set up your environment

To get started, you'll need to install the `dagster` and `dagster-looker` Python packages:

```bash
pip install dagster dagster-looker
```

## Represent Looker assets in the asset graph

To load Looker assets into the Dagster asset graph, you must first construct a <PyObject section="libraries" module="dagster_looker" object="LookerResource" />, which allows Dagster to communicate with your Looker instance. You'll need to supply your Looker instance URL and API credentials, which can be passed directly or accessed from the environment using <PyObject section="resources" module="dagster" object="EnvVar" />.

Dagster can automatically load all views, explores, and dashboards from your Looker instance as asset specs. Call the <PyObject section="libraries" module="dagster_looker" object="load_looker_asset_specs" /> function, which returns a list of <PyObject section="assets" module="dagster" object="AssetSpec" pluralize /> representing your Looker assets. You can then include these asset specs in your <PyObject section="definitions" module="dagster" object="Definitions" /> object:

<CodeExample path="docs_snippets/docs_snippets/integrations/looker/representing-looker-assets.py" />

## Load Looker assets from filtered dashboards and explores

It is possible to load a subset of your Looker assets by providing a <PyObject section="libraries" module="dagster_looker" object="LookerFilter" /> to the <PyObject section="libraries" module="dagster_looker" object="load_looker_asset_specs" /> function. All dashboards contained in the folders provided to your <PyObject section="libraries" module="dagster_looker" object="LookerFilter" /> will be fetched. Additionally, only the explores used in these dashboards will be fetched by passing `only_fetch_explores_used_in_dashboards=True` to your <PyObject section="libraries" module="dagster_looker" object="LookerFilter" />.

Note that the content and size of Looker instance may affect the performance of your Dagster deployments. Filtering the dashboards and explores selection from which your Looker assets will be loaded is particularly useful for improving loading times.

<CodeExample path="docs_snippets/docs_snippets/integrations/looker/filtering-looker-assets.py" />

### Customize asset definition metadata for Looker assets

By default, Dagster will generate asset specs for each Looker asset based on its type, and populate default metadata. You can further customize asset properties by passing a custom <PyObject section="libraries" module="dagster_looker" object="DagsterLookerApiTranslator" /> subclass to the <PyObject section="libraries" module="dagster_looker" object="load_looker_asset_specs" /> function. This subclass can implement methods to customize the asset specs for each Looker asset type.


<CodeExample path="docs_snippets/docs_snippets/integrations/looker/customize-looker-assets.py" />

Note that `super()` is called in each of the overridden methods to generate the default asset spec. It is best practice to generate the default asset spec before customizing it.

### Materialize Looker PDTs from Dagster

You can use Dagster to orchestrate the materialization of Looker PDTs. To model PDTs as assets, build their asset definitions by passing a list of <PyObject section="libraries" module="dagster_looker" object="RequestStartPdtBuild" /> to <PyObject section="libraries" module="dagster_looker" object="build_looker_pdt_assets_definitions" /> function.


<CodeExample path="docs_snippets/docs_snippets/integrations/looker/materializing-looker-pdts.py" />

### Related

- [`dagster-looker` API reference](/api/python-api/libraries/dagster-looker)
- [Asset definitions](/guides/build/assets/defining-assets)
- [Resources](/guides/build/external-resources/)
- [Using environment variables and secrets](/guides/deploy/using-environment-variables-and-secrets)
