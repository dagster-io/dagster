---
title: Ensure data quality with asset checks
description: Ensure assets are correct with asset checks
sidebar_position: 40
---

Data quality is critical in data pipelines. Inspecting individual assets ensures that data quality issues are caught before they affect the entire pipeline.

In Dagster, you define [asset checks](/guides/test/asset-checks) like you define assets. Asset checks run when an asset is materialized. In this step, you will:

- Define an asset check
- Execute that asset check in the UI

## 1. Define an asset check

Our asset check can go in the `assets.py` file next to the asset we just defined. An asset check can be any logic we want. In our case we will 

<CodeExample
  path="docs_snippets/docs_snippets/guides/tutorials/etl_tutorial/src/etl_tutorial/defs/assets.py"
  language="python"
  startAfter="start_asset_check"
  endBefore="end_asset_check"
  title="src/etl_tutorial/defs/assets.py"
/>

:::info
The asset check is using the same `DuckDBResource` resource we defined for the asset. Resources can be shared across all objects in Dagster.
:::

Asset checks will run when an asset is materialized, but asset checks can also be executed manually in the UI:

1. Reload your Definitions.
2. Navigate to the Asset Details page for the `joined_data` asset.
3. Select the "Checks" tab.
4. Click the **Execute** button for `missing_dimension_check`.

# TODO Screenshot

## Summary

<CliInvocationExample path="docs_snippets/docs_snippets/guides/tutorials/etl_tutorial/tree/step-2.txt" />

## Next steps

- Continue this tutorial with [creating and materializing partitioned assets](/etl-pipeline-tutorial/automate-your-pipeline)
