---
title: "Using Sigma with Dagster"
description: Represent your Sigma assets in Dagster
---

:::note

This feature is considered **experimental**

:::

This guide provides instructions for using Dagster with Sigma using the [`dagster-sigma`](/api/python-api/libraries/dagster-sigma) library. Your Sigma assets, including datasets and workbooks, can be represented in the Dagster asset graph, allowing you to track lineage and dependencies between Sigma assets and upstream data assets you are already modeling in Dagster.

## What you'll learn

- How to represent Sigma assets in the Dagster asset graph, including lineage to other Dagster assets.
- How to customize asset definition metadata for these Sigma assets.

<details>
  <summary>Prerequisites</summary>

- The `dagster-sigma` library installed in your environment
- Familiarity with asset definitions and the Dagster asset graph
- Familiarity with Dagster resources
- Familiarity with Sigma concepts, like datasets and workbooks
- A Sigma organization
- A Sigma client ID and client secret. For more information, see [Generate API client credentials](https://help.sigmacomputing.com/reference/generate-client-credentials#generate-api-client-credentials) in the Sigma documentation.

</details>

## Set up your environment

To get started, you'll need to install the `dagster` and `dagster-sigma` Python packages:

```bash
pip install dagster dagster-sigma
```

## Represent Sigma assets in the asset graph

To load Sigma assets into the Dagster asset graph, you must first construct a <PyObject section="libraries" module="dagster_sigma" object="SigmaOrganization" /> resource, which allows Dagster to communicate with your Sigma organization. You'll need to supply your client ID and client secret alongside the base URL. See [Identify your API request URL](https://help.sigmacomputing.com/reference/get-started-sigma-api#identify-your-api-request-url) in the Sigma documentation for more information on how to find your base URL.

Dagster can automatically load all datasets and workbooks from your Sigma workspace as asset specs. Call the <PyObject section="libraries" module="dagster_sigma" object="load_sigma_asset_specs" /> function, which returns list of <PyObject section="assets" module="dagster" object="AssetSpec" />s representing your Sigma assets. You can then include these asset specs in your <PyObject section="definitions" module="dagster" object="Definitions" /> object:

<CodeExample path="docs_snippets/docs_snippets/integrations/sigma/representing-sigma-assets.py" />

## Load Sigma assets from filtered workbooks

It is possible to load a subset of your Sigma assets by providing a <PyObject section="libraries" module="dagster_sigma" object="SigmaFilter" /> to the <PyObject section="libraries" module="dagster_sigma" object="load_sigma_asset_specs" /> function. This `SigmaFilter` object allows you to specify the folders from which you want to load Sigma workbooks, and also will allow you to configure which datasets are represented as assets.

Note that the content and size of Sigma organization may affect the performance of your Dagster deployments. Filtering the workbooks selection from which your Sigma assets will be loaded is particularly useful for improving loading times.

<CodeExample path="docs_snippets/docs_snippets/integrations/sigma/filtering-sigma-assets.py" />

### Customize asset definition metadata for Sigma assets

By default, Dagster will generate asset specs for each Sigma asset based on its type, and populate default metadata. You can further customize asset properties by passing a custom <PyObject section="libraries" module="dagster_sigma" object="DagsterSigmaTranslator" /> subclass to the <PyObject section="libraries" module="dagster_sigma" object="load_sigma_asset_specs" /> function. This subclass can implement methods to customize the asset specs for each Sigma asset type.

<CodeExample path="docs_snippets/docs_snippets/integrations/sigma/customize-sigma-asset-defs.py" />

Note that `super()` is called in each of the overridden methods to generate the default asset spec. It is best practice to generate the default asset spec before customizing it.

### Load Sigma assets from multiple organizations

Definitions from multiple Sigma organizations can be combined by instantiating multiple <PyObject section="libraries" module="dagster_sigma" object="SigmaOrganization" /> resources and merging their specs. This lets you view all your Sigma assets in a single asset graph:

<CodeExample path="docs_snippets/docs_snippets/integrations/sigma/multiple-sigma-organizations.py" />

### Related

- [`dagster-sigma` API reference](/api/python-api/libraries/dagster-sigma)
- [Asset definitions](/guides/build/assets/defining-assets)
- [Resources](/guides/build/external-resources/)
- [Using environment variables and secrets](/guides/deploy/using-environment-variables-and-secrets)
