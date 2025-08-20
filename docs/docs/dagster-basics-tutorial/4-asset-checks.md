---
title: Asset checks
description: Ensuring quality with asset checks
sidebar_position: 60
---

When building data applications, it is important to ensure the quality of all underlying entities. In this step, we will add checks to confirm that our assets are producing the data we expect.

In Dagster, these quality measures are called [asset checks](/guides/test/asset-checks) and are defined in a similar way to assets. When an asset is materialized, asset checks also execute and verify that certain criteria are met based on the logic within the check.

![2048 resolution](/images/tutorial/dagster-tutorial/overviews/asset-checks.png)

## 1. Define an asset check

To create an asset check, define a function and decorate it with the <PyObject section="asset-checks" module="dagster" object="asset_check" decorator />. Within the asset check, set the `asset` parameter to indicate which asset the check runs against.

Here, we will create an asset check for the `orders_aggregation` asset to ensure that there are rows in the underlying DuckDB table:

<CodeExample
  path="docs_snippets/docs_snippets/guides/tutorials/dagster-tutorial/src/dagster_tutorial/defs/assets.py"
  language="python"
  startAfter="start_define_asset_checks"
  endBefore="end_define_asset_checks"
  title="src/dagster_tutorial/defs/assets.py"
/>

This asset check queries the table directly to determine if the data is valid. Based on the query result, it sets the <PyObject section="asset-checks" module="dagster" object="AssetCheckResult" /> to pass or fail.

:::info

The asset check uses the same `DuckDBResource` resource we defined for our assets. Resources can be shared across all objects in Dagster.

:::

## 2. Checking our asset check runs

In the Dagster UI at [http://127.0.0.1:3000](http://127.0.0.1:3000), you should now see an asset check associated with the `orders_aggregation` asset:

![2048 resolution](/images/tutorial/dagster-tutorial/asset-check-1.png)

Asset checks run automatically when an asset is materialized, but you can also execute them manually in the UI:

1. Reload your Definitions.
2. Navigate to the **Asset Details** page for the `orders_aggregation` asset.
3. Select the **Checks** tab.
4. Click **Execute** for `orders_aggregation` (assuming the asset has already been materialized).

   ![2048 resolution](/images/tutorial/dagster-tutorial/asset-check-2.png)
