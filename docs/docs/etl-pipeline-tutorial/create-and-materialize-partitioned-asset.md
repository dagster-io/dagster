---
title: Create and materialize partitioned assets
description: Partitioning Assets by datetime and categories
last_update:
  date: 2024-11-25
  author: Alex Noonan
sidebar_position: 40
---

[Partitions](/guides/build/partitions-and-backfills/partitioning-assets) are a core abstraction in Dagster, that allow you to manage large datasets, process incremental updates, and improve pipeline performance. You can partition assets the following ways:

- Time-based: Split data by time periods (e.g., daily, monthly)
- Category-based: Divide by known categories (e.g., country, product type)
- Two-dimensional: Combine two partition types (e.g., country + date)
- Dynamic: Create partitions based on runtime conditions

In this step, you will:

- Create a time-based asset partitioned by month
- Create a category-based asset partitioned by product category

## 1. Create a time-based partitioned asset

Dagster natively supports partitioning assets by datetime groups. We want to create an asset that calculates the monthly performance for each sales rep. To create the monthly partition copy the following code below the `missing_dimension_check` asset check.

<CodeExample
  path="docs_snippets/docs_snippets/guides/tutorials/etl_tutorial/defs/assets.py"
  language="python"
  startAfter="start_monthly_partition"
  endBefore="end_monthly_partition"
/>

Partition data are accessed within an asset by context. We want to create an asset that does this calculation for a given month from the partition
and deletes any previous value for that month. Copy the following asset under the `monthly_partition` we just created.

<CodeExample
  path="docs_snippets/docs_snippets/guides/tutorials/etl_tutorial/defs/assets.py"
  language="python"
  startAfter="start_monthly_sales_performance_asset"
  endBefore="end_monthly_sales_performance_asset"
/>

:::info
Do not worry about the `automation_condition` in the `dg.asset` decorator for now. This is not necessary but will make more sense when we discuss automation later.
:::

## 2. Create a category-based partitioned asset

Using known defined partitions is a simple way to break up your dataset when you know the different groups you want to subset it by. In our pipeline, we want to create an asset that represents the performance of each product category.

1. To create the statically-defined partition for the product category, copy this code beneath the `monthly_sales_performance` asset:

<CodeExample
  path="docs_snippets/docs_snippets/guides/tutorials/etl_tutorial/defs/assets.py"
  language="python"
  startAfter="start_product_category_partition"
  endBefore="end_product_category_partition"
/>

2. Now that the partition has been defined, we can use that in an asset that calculates the product category performance:

<CodeExample
  path="docs_snippets/docs_snippets/guides/tutorials/etl_tutorial/defs/assets.py"
  language="python"
  startAfter="start_product_performance_asset"
  endBefore="end_product_performance_asset"
/>

## 3. Materialize partitioned assets

To materialize these assets:

1. Navigate to the assets page.
2. Reload definitions.
3. Select the `monthly_sales_performance` asset, then **Materialize selected**.
4. Ensure all partitions are selected, then launch a backfill.
5. Select the `product_performance` asset, then **Materialize selected**.
6. Ensure all partitions are selected, then launch a backfill.

## Next steps

Now that we have the main assets in our ETL pipeline, it's time to add [automation to our pipeline](/etl-pipeline-tutorial/automate-your-pipeline)
