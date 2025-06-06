---
title: Ensure data quality with asset checks
description: Ensure assets are correct with asset checks
sidebar_position: 60
---

Data quality is critical in data pipelines. Inspecting individual assets ensures that data quality issues are caught before they affect the entire pipeline.

In Dagster, you define [asset checks](/guides/test/asset-checks) like you define assets. Asset checks run when an asset is materialized. In this step you will:

- Define an asset check
- Execute that asset check in the UI

## 1. Define an asset check

In this case we want to create a check to identify if there are any rows in `joined_data` that are missing a value for `rep_name` or `product_name`.

Copy the following code beneath the `joined_data` asset.

<CodeExample
  path="docs_snippets/docs_snippets/guides/tutorials/etl_tutorial_components/src/etl_tutorial_components/defs/assets.py"
  language="python"
  startAfter="start_asset_check"
  endBefore="end_asset_check"
  title="src/etl_tutorial_components/defs/assets.py"
/>

Asset checks will run when an asset is materialized, but asset checks can also be executed manually in the UI:

1. Reload your Definitions.
2. Navigate to the Asset Details page for the `joined_data` asset.
3. Select the "Checks" tab.
4. Click the **Execute** button for `missing_dimension_check`.

![2048 resolution](/images/tutorial/etl-tutorial/asset-check.png)

## Next steps

- Continue this tutorial with [creating and materializing partitioned assets](/etl-pipeline-tutorial/create-and-materialize-partitioned-asset)