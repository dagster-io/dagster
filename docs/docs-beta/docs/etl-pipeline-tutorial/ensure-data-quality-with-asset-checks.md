---
title: Ensure data quality with asset checks
description: Ensure assets are correct with asset checks
last_update:
  author: Alex Noonan
sidebar_position: 40
---

Data quality is critical in data pipelines. Inspecting individual assets ensures that data quality issues are caught before they affect the entire pipeline.

In Dagster, you define [asset checks](/guides/test/asset-checks) like you define assets. Asset checks run when an asset is materialized. In this step you will:

- Define an asset check
- Execute that asset check in the UI

## 1. Define an asset check

In this case we want to create a check to identify if there are any rows in `joined_data` that are missing a value for `rep_name` or `product_name`. 

Copy the following code beneath the `joined_data` asset.

<CodeExample filePath="guides/tutorials/etl_tutorial/etl_tutorial/definitions.py" language="python" lineStart="134" lineEnd="150"/>

## 2. Run the asset check

Before you can run the asset check, you need to add it to the Definitions object. Like assets, asset checks are added to their own list.

Your Definitions object should look like this now:

```python
defs = dg.Definitions(
    assets=[products,
        sales_reps,
        sales_data,
        joined_data,
    ],
    asset_checks=[missing_dimension_check],
    resources={"duckdb": DuckDBResource(database="data/mydb.duckdb")},
)
```
Asset checks will run when an asset is materialized, but asset checks can also be executed manually in the UI:

1. Reload your Definitions.
2. Navigate to the Asset Details page for the `joined_data` asset.
3. Select the "Checks" tab.
4. Click the **Execute** button for `missing_dimension_check`.

  ![2048 resolution](/images/tutorial/etl-tutorial/asset-check.png)

## Next steps

- Continue this tutorial with [Asset Checks](create-and-materialize-partitioned-asset)