---
title: Partitions
description: Partitioning the data in assets
sidebar_position: 70
unlisted: true
---

[Partitions](/guides/build/partitions-and-backfills/partitioning-assets) are a core abstraction in Dagster that allow you to manage large datasets, process incremental updates, and improve pipeline performance. Assets can be partitioned in several ways:

- **Time-based**: Split data by time periods (e.g., daily, monthly).
- **Category-based**: Divide by known categories (e.g., country, product type).
- **Two-dimensional**: Combine two partition types (e.g., country + date).
- **Dynamic**: Create partitions based on runtime conditions.

## 1. Create a time-based partitioned asset

When an asset is partitioned, it still appears as a single asset in the asset graph, but it is defined by multiple underlying partitions. In this step, we will create a new asset that calculates the monthly performance for each sales rep. Before defining the asset, we must define the partition.

Dagster natively supports partitioning assets by datetime groups. To create a monthly partition, add the following:

<CodeExample
  path="docs_snippets/docs_snippets/guides/tutorials/dagster-tutorial/src/dagster_tutorial/defs/assets.py"
  language="python"
  startAfter="start_define_monthly_partition"
  endBefore="end_define_monthly_partition"
  title="src/dagster_tutorial/defs/assets.py"
/>

Next, update the `orders_by_month` asset to use this partition:

<CodeExample
  path="docs_snippets/docs_snippets/guides/tutorials/dagster-tutorial/src/dagster_tutorial/defs/assets.py"
  language="python"
  startAfter="start_define_assets_with_partitions"
  endBefore="end_define_assets_with_partitions"
  title="src/dagster_tutorial/defs/assets.py"
/>

Partitions are accessed through the `context` object, which is passed to each asset during execution and provides runtime information. When running an asset for a specific partition date, you can reference that value using `context.partition_key`. The rest of the implementation should follow the same pattern as the other assets we have defined.

In this case, we are creating a new table, `orders_by_month`. We first delete any existing data for the current partition, then insert new data for that partition. This ensures that our pipeline is [idempotent](https://en.wikipedia.org/wiki/Idempotence), allowing us to re-execute the same partition without duplicating data.

## 2. Materialize partitioned assets

To materialize these assets:

1. Navigate to the **Assets** page.
2. Reload your Definitions.
3. Select the `orders_by_month` asset, then click **Materialize selected**.

   When materializing a partitioned asset, you must select which partitions to execute. Because our partition has a start date (`"2018-01-01"`) and no end date, there will be partitions for every month starting from 2018. Select only the partitions for the first four months of 2018:

   ```
   [2018-01-01...2018-05-01]
   ```

4. Launch a backfill. After execution finishes, you can view the subset of total partitions that have executed.

#TODO Screenshot
