---
layout: Integration
status: published
name: Looker
title: Dagster & Looker
sidebar_label: Looker
excerpt: The Looker integration allows you to monitor your Looker project as assets in Dagster, along with other data assets.
date: 2024-08-30
apireflink: https://docs.dagster.io/api/python-api/libraries/dagster-looker
docslink: https://docs.dagster.io/integrations/libraries/looker/
partnerlink: https://www.looker.com/
communityIntegration: true
categories:
  - BI
enabledBy:
enables:
tags: [dagster-supported, bi]
sidebar_custom_props:
  logo: images/integrations/looker.svg
---

import Beta from '@site/docs/partials/\_Beta.md';

<Beta />

Dagster allows you to represent your Looker project as assets, alongside other your other technologies like dbt and Sling. This allows you to see how your Looker assets are connected to your other data assets, and how changes to other data assets might impact your Looker project.

### Installation

```bash
pip install dagster-looker
```

### Represent Looker assets in the asset graph

To load Looker assets into the Dagster asset graph, you must first construct a <PyObject section="libraries" module="dagster_looker" object="LookerResource" />, which allows Dagster to communicate with your Looker instance. You'll need to supply your Looker instance URL and API credentials, which can be passed directly or accessed from the environment using <PyObject section="resources" module="dagster" object="EnvVar" />.

Dagster can automatically load all views, explores, and dashboards from your Looker instance as asset specs. Call the <PyObject section="libraries" module="dagster_looker" object="load_looker_asset_specs" /> function, which returns a list of <PyObject section="assets" module="dagster" object="AssetSpec" pluralize /> representing your Looker assets. You can then include these asset specs in your <PyObject section="definitions" module="dagster" object="Definitions" /> object:

<CodeExample path="docs_snippets/docs_snippets/integrations/looker/asset_graph.py" language="python" />

### Load Looker assets from filtered dashboards and explores

It is possible to load a subset of your Looker assets by providing a <PyObject section="libraries" module="dagster_looker" object="LookerFilter" /> to the <PyObject section="libraries" module="dagster_looker" object="load_looker_asset_specs" /> function. All dashboards contained in the folders provided to your <PyObject section="libraries" module="dagster_looker" object="LookerFilter" /> will be fetched. Additionally, only the explores used in these dashboards will be fetched by passing only_fetch_explores_used_in_dashboards=True to your <PyObject section="libraries" module="dagster_looker" object="LookerFilter" />.

Note that the content and size of Looker instance may affect the performance of your Dagster deployments. Filtering the dashboards and explores selection from which your Looker assets will be loaded is particularly useful for improving loading times.

### Customize asset definition metadata for Looker assets

<CodeExample path="docs_snippets/docs_snippets/integrations/looker/asset_graph_filtered.py" language="python" />

By default, Dagster will generate asset specs for each Looker asset based on its type, and populate default metadata. You can further customize asset properties by passing a custom <PyObject section="libraries" module="dagster_looker" object="DagsterLookerApiTranslator" /> subclass to the <PyObject section="libraries" module="dagster_looker" object="load_looker_asset_specs" /> function. This subclass can implement methods to customize the asset specs for each Looker asset type.

<CodeExample path="docs_snippets/docs_snippets/integrations/looker/asset_metadata.py" language="python" />

Note that `super()` is called in each of the overridden methods to generate the default asset spec. It is best practice to generate the default asset spec before customizing it.

### Materialize Looker PDTs from Dagster

You can use Dagster to orchestrate the materialization of Looker PDTs. To model PDTs as assets, build their asset definitions by passing a list of <PyObject section="libraries" module="dagster_looker" object="RequestStartPdtBuild" /> to <PyObject section="libraries" module="dagster_looker" object="build_looker_pdt_assets_definitions" /> function.

<CodeExample path="docs_snippets/docs_snippets/integrations/looker/pdts.py" language="python" />

### About Looker

**Looker** is a modern platform for data analytics and visualization. It provides a unified interface for data exploration, modeling, and visualization, making it easier to understand and analyze data. Looker integrates with various data sources and can be used to create interactive reports, dashboards, and visualizations.
