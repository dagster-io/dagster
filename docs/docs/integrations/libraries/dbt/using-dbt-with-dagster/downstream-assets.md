---
title: "Add a downstream asset"
description: Dagster can orchestrate dbt alongside other technologies.
sidebar_position: 400
---

By this point, you've [set up a dbt project](set-up-dbt-project), [loaded dbt models into Dagster as assets](load-dbt-models), and [defined assets upstream of your dbt models](upstream-assets).

In this step, you'll:

- [Install the plotly library](#step-1-install-the-plotly-library)
- [Define a downstream asset that computes a chart using plotly](#step-2-define-the-order_count_chart-asset)
- [Materialize the `order_count_chart` asset](#step-3-materialize-the-order_count_chart-asset)

## Step 1: Install the plotly library

```shell
pip install plotly
```

## Step 2: Define the order_count_chart asset

You've added upstream assets to your data pipeline, but nothing downstream - until now. In this step, you'll define a Dagster asset called `order_count_chart` that uses the data in the `customers` dbt model to computes a plotly chart of the number of orders per customer.

Like the `raw_customers` asset that we added in the [previous section](upstream-assets#step-2-define-an-upstream-dagster-asset), we'll put this asset in our `assets.py` file, inside the `jaffle_dagster` directory.

To add the `order_count_chart` asset:

1. Replace the imports section with the following:

   <CodeExample path="docs_snippets/docs_snippets/integrations/dbt/tutorial/downstream_assets/assets.py" startAfter="start_imports" endBefore="end_imports" />

   This adds an import for plotly, as well as <PyObject section="libraries" module="dagster_dbt" object="get_asset_key_for_model" /> and <PyObject section="metadata" module="dagster" object="MetadataValue" />, which we'll use in our asset.

2. After your definition of `jaffle_shop_dbt_assets`, add the definition for the `order_count_chart` asset:

   <CodeExample path="docs_snippets/docs_snippets/integrations/dbt/tutorial/downstream_assets/assets.py" startAfter="start_downstream_asset" endBefore="end_downstream_asset" />

   This asset definition looks similar the asset we defined in the previous section. In this case, instead of fetching data from an external source and writing it to DuckDB, it reads data from DuckDB, and then uses it to make a plot.

   The line `deps=[get_asset_key_for_model([jaffle_shop_dbt_assets], "customers")]` tells Dagster that this asset is downstream of the `customers` dbt model. This dependency will be displayed as such in Dagster's UI. If you launch a run to materialize both of them, Dagster won't run `order_count_chart` until `customers` completes.

3. Add the `order_count_chart` to the `Definitions`:

   <CodeExample path="docs_snippets/docs_snippets/integrations/dbt/tutorial/downstream_assets/definitions.py" startAfter="start_defs" endBefore="end_defs" />

## Step 3: Materialize the order_count_chart asset

If the Dagster UI is still running from the previous section, click the "Reload Definitions" button in the upper right corner. If you shut it down, then you can launch it again with the same command from the previous section:

```shell
dagster dev
```

The UI will look like this:

![Asset group with dbt models and Python asset](/images/integrations/dbt/using-dbt-with-dagster/downstream-assets/asset-graph.png)

A new asset named `order_count_chart` is at the bottom, downstream of the `customers` asset. Click on `order_count_chart` and click **Materialize selected**.

That's it! When the run successfully completes, the following chart will automatically open in your browser:

![plotly chart asset displayed in Chrome](/images/integrations/dbt/using-dbt-with-dagster/downstream-assets/order-count-chart.png)

## What's next?

That's the end of this tutorial - congratulations! By now, you should have a working dbt and Dagster integration and a handful of materialized Dagster assets.

What's next? From here, you can:

- Learn more about [asset definitions](/guides/build/assets/)
- Learn how to [build jobs that materialize dbt assets](/integrations/libraries/dbt/reference#scheduling-dbt-jobs)
- Get a [deeper understanding of Dagster's dbt integration](/integrations/libraries/dbt/reference)
- Check out the [`dagster-dbt` API docs](/api/python-api/libraries/dagster-dbt)
