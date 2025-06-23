---
title: Create and materialize partitioned assets
description: Partitioning Assets by datetime and categories
sidebar_position: 50
---

[Partitions](/guides/build/partitions-and-backfills/partitioning-assets) are a core abstraction in Dagster, that allow you to manage large datasets, process incremental updates, and improve pipeline performance. You can partition assets the following ways:

- Time-based: Split data by time periods (e.g., daily, monthly)
- Category-based: Divide by known categories (e.g., country, product type)
- Two-dimensional: Combine two partition types (e.g., country + date)
- Dynamic: Create partitions based on runtime conditions

In this step, you will:

- Create a time-based asset partitioned by month

## 1. Create a time-based partitioned asset

Dagster natively supports partitioning assets by datetime groups. We want to create an asset that calculates the monthly performance for each sales rep. To create the monthly partition copy the following code below the `missing_dimension_check` asset check in the `assets.py`.

<CodeExample
  path="docs_snippets/docs_snippets/guides/tutorials/etl_tutorial/src/etl_tutorial/defs/assets.py"
  language="python"
  startAfter="start_monthly_partition"
  endBefore="end_monthly_partition"
  title="src/etl_tutorial/defs/assets.py"
/>

Partition data are accessed within an asset by context. We want to create an asset that does this calculation for a given month from the partition
and deletes any previous value for that month. Copy the following asset under the `monthly_partition` we just created.

<CodeExample
  path="docs_snippets/docs_snippets/guides/tutorials/etl_tutorial/src/etl_tutorial/defs/assets.py"
  language="python"
  startAfter="start_monthly_sales_performance_asset"
  endBefore="end_monthly_sales_performance_asset"
  title="src/etl_tutorial/defs/assets.py"
/>

:::info
Do not worry about the `automation_condition` in the `dg.asset` decorator for now. This is not necessary but will make more sense when we discuss automation later.
:::

## 2. Materialize partitioned assets

To materialize these assets:

1. Navigate to the assets page.
2. Reload definitions.
3. Select the `monthly_sales_performance` asset, then **Materialize selected**.

   When launching a partitioned asset, you will need to select the which partitions to execute. Because our partition has a start date (`"2018-01-01"`) and no end date, there will be partitions for every month from 2018. Only select partitions for the first four months of 2018. 

   ```
   [2018-01-01...2018-05-01]
   ```

4. Launch a backfill. After the execution is finished you can see the subset of total partitions that have executed.

   ![2048 resolution](/images/tutorial/etl-tutorial/asset-partition-execution.png)

## Summary

Partitions provide operational flexibility by allowing you to launch runs that materialize only a subset of your data without affecting the rest, and support backfilling capabilities to reprocess historical data for specific time periods or categories. As you are developing assets, consider where partitions might be helpful.

## Next steps

Now that we have the main assets in our ETL pipeline, it's time to add [automation your pipeline](/etl-pipeline-tutorial/automate-your-pipeline)
