---
title: Ensuring data quality with asset checks
description: Ensure assets are correct with asset checks
last_update:
  author: Alex Noonan
---

# Asset checks

Data Quality is critical in data pipelines. Much like in a factory producing cars, inspecting parts after they complete certain steps ensures that defects are caught before the car is completely assembled. 

In Dagster, you define [asset checks](/guides/test/asset-checks) in a similar way that you would define an Asset. In this step you will:

- Define an asset check
- Execute that asset check in the UI

## 1. Define the Asset CHeck

In this case we want to create a check to identify if there are any rows that have a product or sales rep that are not in the `joined_data` table. 

Paste the following code beneath the `joined_data` asset.

<CodeExample filePath="guides/tutorials/etl_tutorial/etl_tutorial/definitions.py" language="python" lineStart="134" lineEnd="149"/>

## 2. Run the asset Check

Before the asset check can be ran it needs to be added to the definitions object. Asset checks are added to their own list like assets. 

Your definitions object should look like this now:

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
Asset checks will run when an asset is materialized, but asset checks can also be executed manually in the UI.

1. Reload Definitions
2. Navigate to the Asset Details page for the `joined_data` asset.
3. Select the checks tab.
4. Press the execute button in for `missing_dimension_check`

  ![2048 resolution](/images/tutorial/etl-tutorial/asset-check.png)

## Next steps

- Continue this tutorial with [Asset Checks](/tutorial/etl-tutorial/04-ensuring-data-quality-with-asset-checks)