---
layout: Integration
status: published
name: Tableau
title: Dagster & Tableau
sidebar_label: Tableau
excerpt: See and understand your data with Tableau through Dagster.
date:
apireflink: https://docs.dagster.io/api/python-api/libraries/dagster-tableau
docslink:
partnerlink:
categories:
  - Other
enabledBy:
enables:
tags: [dagster-supported, bi]
sidebar_custom_props:
  logo: images/integrations/tableau.svg
---

import Beta from '@site/docs/partials/\_Beta.md';

<Beta />

This guide provides instructions for using Dagster with Tableau using the `dagster-tableau` library. Your Tableau assets, such as data sources, sheets, and dashboards, can be represented in the Dagster asset graph, allowing you to track lineage and dependencies between Tableau assets and upstream data assets you are already modeling in Dagster.

## What you'll learn

- How to represent Tableau assets in the Dagster asset graph.

- How to customize asset definition metadata for these Tableau assets.

- How to refresh Tableau workbooks.

- How to materialize Tableau sheets and dashboards.

<details>
  <summary>Prerequisites</summary>

- The `dagster-tableau` library installed in your environment
- Familiarity with asset definitions and the Dagster asset graph
- Familiarity with Dagster resources
- Familiarity with Tableau concepts, like data sources, sheets, and dashboards
- A Tableau site, either on Tableau Cloud or Tableau Server
- A connected app configured to access Tableau. For more information, see [Use Tableau Connected Apps for Application Integration](https://help.tableau.com/current/online/en-us/connected_apps.htm) in the Tableau documentation.

</details>

## Set up your environment

To get started, you'll need to install the `dagster` and `dagster-tableau` Python packages:

```bash
pip install dagster dagster-tableau
```

## Represent Tableau assets in the asset graph

To load Tableau assets into the Dagster asset graph, you must first construct a Tableau resource, which allows Dagster to communicate with your Tableau workspace. The Tableau resource to create depends on your Tableau deployment type - use <PyObject section="libraries" module="dagster_tableau" object="TableauCloudWorkspace" /> if you are using Tableau Cloud or <PyObject section="libraries" module="dagster_tableau" object="TableauServerWorkspace" /> if you are using Tableau Server. To connect to the Tableau workspace, you'll need to [configure a connected app with direct trust](https://help.tableau.com/current/online/en-gb/connected_apps_direct.htm) in Tableau, then supply your Tableau site information and connected app credentials to the resource. The Tableau resource uses the JSON Web Token (JWT) authentication to connect to the Tableau workspace.

Dagster can automatically load all data sources, sheets, and dashboards from your Tableau workspace as asset specs. Call the <PyObject section="libraries" module="dagster_tableau" object="load_tableau_asset_specs" /> function, which returns a list of <PyObject section="assets" module="dagster" object="AssetSpec" pluralize /> representing your Tableau assets. You can then include these asset specs in your <PyObject section="definitions" module="dagster" object="Definitions" /> object:

<Tabs>
<TabItem value="Using Dagster with Tableau Cloud">

Use <PyObject section="libraries" module="dagster_tableau" object="TableauCloudWorkspace" /> to interact with your Tableau Cloud workspace:

<CodeExample path="docs_snippets/docs_snippets/integrations/tableau/representing-tableau-cloud-assets.py" />

</TabItem>
<TabItem value="Using Dagster with Tableau Server">

Use <PyObject section="libraries" module="dagster_tableau" object="TableauServerWorkspace" /> to interact with your Tableau Server workspace:

<CodeExample path="docs_snippets/docs_snippets/integrations/tableau/representing-tableau-server-assets.py" />

</TabItem>
</Tabs>

### Customize asset definition metadata for Tableau assets

By default, Dagster will generate asset specs for each Tableau asset based on its type, and populate default metadata. You can further customize asset properties by passing a custom <PyObject section="libraries" module="dagster_tableau" object="DagsterTableauTranslator" /> subclass to the <PyObject section="libraries" module="dagster_tableau" object="load_tableau_asset_specs" /> function. This subclass can implement methods to customize the asset specs for each Tableau asset type.

<CodeExample path="docs_snippets/docs_snippets/integrations/tableau/customize-tableau-asset-defs.py" />

Note that `super()` is called in each of the overridden methods to generate the default asset spec. It is best practice to generate the default asset spec before customizing it.

### Load Tableau assets from multiple workspaces

Definitions from multiple Tableau workspaces can be combined by instantiating multiple Tableau resources and merging their specs. This lets you view all your Tableau assets in a single asset graph:

<CodeExample path="docs_snippets/docs_snippets/integrations/tableau/multiple-tableau-workspaces.py" />
from dagster_tableau import TableauCloudWorkspace, load_tableau_asset_specs

### Refresh and materialize Tableau assets

You can use Dagster to refresh Tableau workbooks and materialize Tableau sheets and dashboards.

<CodeExample path="docs_snippets/docs_snippets/integrations/tableau/refresh-and-materialize-tableau-assets.py" />

Note that only workbooks created with extracts can be refreshed using this method. See more about [refreshing data sources](https://help.tableau.com/current/pro/desktop/en-us/refreshing_data.htm) in Tableau documentation website.

### Add a Data Quality Warning in Tableau using a sensor

When an upstream dependency of a Tableau asset fails to materialize or to pass the asset checks, it is possible to add a [Data Quality Warning](https://help.tableau.com/current/online/en-us/dm_dqw.htm) to the corresponding data source in Tableau. This can be achieved by leveraging the `add_data_quality_warning_to_data_source` in a sensor.

<CodeExample path="docs_snippets/docs_snippets/integrations/tableau/add-tableau-data-quality-warning.py" />

### Customizing how Tableau assets are materialized

Instead of using the out-of-the-box <PyObject section="libraries" module="dagster_tableau" object="build_tableau_materializable_assets_definition" /> utility, you can build your own assets definition that trigger the refresh of your Tableau workbooks. This allows you to customize how the refresh is triggered or to run custom code before or after the refresh.

<CodeExample path="docs_snippets/docs_snippets/integrations/tableau/materialize-tableau-assets-advanced.py" />
from collections.abc import Sequence

### Related

- [`dagster-tableau` API reference](/api/python-api/libraries/dagster-tableau)
- [Asset definitions](/guides/build/assets/)
- [Resources](/guides/build/external-resources/)
- [Using environment variables and secrets](/guides/deploy/using-environment-variables-and-secrets)
