---
title: Dagster & Power BI
sidebar_label: Power BI
description: Your Power BI assets, such as semantic models, data sources, reports, and dashboards, can be represented in the Dagster asset graph, allowing you to track lineage and dependencies between Power BI assets and upstream data assets you are already modeling in Dagster. You can also use Dagster to orchestrate Power BI semantic models, allowing you to trigger refreshes of these models on a cadence or based on upstream data changes.
tags: [dagster-supported, bi]
source: https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-powerbi
pypi: https://pypi.org/project/dagster-powerbi
sidebar_custom_props:
  logo: images/integrations/powerbi.svg
partnerlink: https://learn.microsoft.com/en-us/power-bi/
---

import Beta from '@site/docs/partials/\_Beta.md';

<Beta />

<p>{frontMatter.description}</p>

## What you'll learn

- How to represent Power BI assets in the Dagster asset graph, including lineage to other Dagster assets.
- How to customize asset definition metadata for these Power BI assets.
- How to materialize Power BI semantic models from Dagster.
- How to customize how Power BI semantic models are materialized.

<details>
  <summary>Prerequisites</summary>

- The `dagster` and `dagster-powerbi` libraries installed in your environment
- Familiarity with asset definitions and the Dagster asset graph
- Familiarity with Dagster resources
- Familiarity with Power BI concepts, like semantic models, data sources, reports, and dashboards
- A Power BI workspace
- A service principal configured to access Power BI, or an API access token. For more information, see [Embed Power BI content with service principal and an application secret](https://learn.microsoft.com/en-us/power-bi/developer/embedded/embed-service-principal) in the Power BI documentation.

</details>

## Set up your environment

To get started, you'll need to install the `dagster` and `dagster-powerbi` Python packages:

<PackageInstallInstructions packageName="dagster-powerbi" />

## Represent Power BI assets in the asset graph

To load Power BI assets into the Dagster asset graph, you must first construct a <PyObject section="libraries" module="dagster_powerbi" object="PowerBIWorkspace" /> resource, which allows Dagster to communicate with your Power BI workspace. You'll need to supply your workspace ID and credentials. You may configure a service principal or use an API access token, which can be passed directly or accessed from the environment using <PyObject section="resources" module="dagster" object="EnvVar" />.

Dagster can automatically load all semantic models, data sources, reports, and dashboards from your Power BI workspace as asset specs. Call the <PyObject section="libraries" module="dagster_powerbi" object="load_powerbi_asset_specs" /> function, which returns a list of <PyObject section="assets" module="dagster" object="AssetSpec" />s representing your Power BI assets. You can then include these asset specs in your <PyObject section="definitions" module="dagster" object="Definitions" /> object:

<CodeExample path="docs_snippets/docs_snippets/integrations/power-bi/representing-power-bi-assets.py" />

By default, Dagster will attempt to snapshot your entire workspace using Power BI's [metadata scanner APIs](https://learn.microsoft.com/en-us/fabric/governance/metadata-scanning-overview), which are able to retrieve more detailed information about your Power BI assets, but rely on the workspace being configured to allow this access.

If you encounter issues with the scanner APIs, you may disable them using `load_powerbi_asset_specs(power_bi_workspace, use_workspace_scan=False)`.

## Customize asset definition metadata for Power BI assets

By default, Dagster will generate asset specs for each Power BI asset based on its type, and populate default metadata. You can further customize asset properties by passing a custom <PyObject section="libraries" module="dagster_powerbi" object="DagsterPowerBITranslator" /> subclass to the <PyObject section="libraries" module="dagster_powerbi" object="load_powerbi_asset_specs" /> function. This subclass can implement methods to customize the asset specs for each Power BI asset type.

<CodeExample path="docs_snippets/docs_snippets/integrations/power-bi/customize-power-bi-asset-defs.py" />

Note that `super()` is called in each of the overridden methods to generate the default asset spec. It is best practice to generate the default asset spec before customizing it.

## Load Power BI assets from multiple workspaces

Definitions from multiple Power BI workspaces can be combined by instantiating multiple <PyObject section="libraries" module="dagster_powerbi" object="PowerBIWorkspace" /> resources and merging their specs. This lets you view all your Power BI assets in a single asset graph:

<CodeExample path="docs_snippets/docs_snippets/integrations/power-bi/multiple-power-bi-workspaces.py" />

## Materialize Power BI semantic models from Dagster

Dagster's default behavior is to pull in representations of Power BI semantic models as external assets, which appear in the asset graph but can't be materialized. However, you can build executable asset definitions that trigger the refresh of Power BI semantic models. The <PyObject section="libraries" module="dagster_powerbi" object="build_semantic_model_refresh_asset_definition" /> utility will construct an asset definition that triggers a refresh of a semantic model when materialized.

<CodeExample path="docs_snippets/docs_snippets/integrations/power-bi/materialize-semantic-models.py" />

You can then add these semantic models to jobs or as targets of Dagster sensors or schedules to trigger refreshes of the models on a cadence or based on other conditions.

## Customizing how Power BI semantic models are materialized

Instead of using the out-of-the-box <PyObject section="libraries" module="dagster_powerbi" object="build_semantic_model_refresh_asset_definition" /> utility, you can build your own asset definitions that trigger the refresh of Power BI semantic models. This allows you to customize how the refresh is triggered or to run custom code before or after the refresh.

<CodeExample path="docs_snippets/docs_snippets/integrations/power-bi/materialize-semantic-models-advanced.py" />

## Customize upstream dependencies

By default, Dagster sets upstream dependencies when generating asset specs for your PowerBI assets. To do so, Dagster parses information about assets that are upstream of specific PowerBI assets from the PowerBI workspace itself. You can customize how upstream dependencies are set on your PowerBI assets by passing an instance of the custom <PyObject section="libraries" module="dagster_powerbi" object="DagsterPowerBITranslator" /> to the <PyObject section="libraries" module="dagster_powerbi" object="load_powerbi_asset_specs" /> function.

The below example defines `my_upstream_asset` as an upstream dependency of `my_powerbi_semantic_model`:

<CodeExample
  startAfter="start_upstream_asset"
  endBefore="end_upstream_asset"
  path="docs_snippets/docs_snippets/integrations/power-bi/customize_upstream_dependencies.py"
/>

Note that `super()` is called in each of the overridden methods to generate the default asset spec. It is best practice to generate the default asset spec before customizing it.
