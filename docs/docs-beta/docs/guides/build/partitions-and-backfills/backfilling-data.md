---
title: Backfilling data
description: Dagster supports data backfills for each partition or subsets of partitions.
sidebar_position: 300
---

Backfilling is the process of running partitions for assets that either don't exist or updating existing records. Dagster supports backfills for each partition or a subset of partitions.

After defining a [partition](partitioning-assets), you can launch a backfill that will submit runs to fill in multiple partitions at the same time.

Backfills are common when setting up a pipeline for the first time. The assets you want to materialize might have historical data that needs to be materialized to get the assets up to date. Another common reason to run a backfill is when you've changed the logic for an asset and need to update historical data with the new logic.

## Launching backfills for partitioned assets

To launch backfills for a partitioned asset, click the **Materialize** button on either the **Asset details** or the **Global asset lineage** page. The backfill modal will display.

Backfills can also be launched for a selection of partitioned assets as long as the most upstream assets share the same partitioning. For example: All partitions use a `DailyPartitionsDefinition`.

![Backfills launch modal](/images/guides/build/partitions-and-backfills/asset-backfill-partition-selection-modal.png)

To observe the progress of an asset backfill, navigate to the **Runs details** page for the run. This page can be accessed by clicking **Runs tab**, then clicking the ID of the run. To see all runs, including runs launched by a backfill, check the **Show runs within backfills** box:

![Asset backfill details page](/images/guides/build/partitions-and-backfills/asset-backfill-details-page.png)

## Launching single-run backfills using backfill policies (experimental)

By default, if you launch a backfill that covers `N` partitions, Dagster will launch `N` separate runs, one for each partition. This approach can help avoid overwhelming Dagster or resources with large amounts of data. However, if you're using a parallel-processing engine like Spark and Snowflake, you often don't need Dagster to help with parallelism, so splitting up the backfill into multiple runs just adds extra overhead.

Dagster supports backfills that execute as a single run that covers a range of partitions, such as executing a backfill as a single Snowflake query. After the run completes, Dagster will track that all the partitions have been filled.

:::note

Single-run backfills only work if they are launched from the asset graph or
asset page, or if the assets are part of an asset job that shares the same
backfill policy across all included assets.

:::

To get this behavior, you need to:

- **Set the asset's `backfill_policy` (<PyObject section="partitions" module="dagster" object="BackfillPolicy" />)** to `single_run`
- **Write code that operates on a range of partitions** instead of just single partitions. This means that, if your code uses the `partition_key` context property, you'll need to update it to use one of the following properties instead:

  - [`partition_time_window`](/api/python-api/execution#dagster.OpExecutionContext.partition_time_window)
  - [`partition_key_range`](/api/python-api/execution#dagster.OpExecutionContext.partition_key_range)
  - [`partition_keys`](/api/python-api/execution#dagster.OpExecutionContext.partition_keys)

  Which property to use depends on whether it's most convenient for you to operate on start/end datetime objects, start/end partition keys, or a list of partition keys.


```python file=/concepts/partitions_schedules_sensors/backfills/single_run_backfill_asset.py startafter=start_marker endbefore=end_marker
from dagster import (
    AssetExecutionContext,
    AssetKey,
    BackfillPolicy,
    DailyPartitionsDefinition,
    asset,
)


@asset(
    partitions_def=DailyPartitionsDefinition(start_date="2020-01-01"),
    backfill_policy=BackfillPolicy.single_run(),
    deps=[AssetKey("raw_events")],
)
def events(context: AssetExecutionContext) -> None:
    start_datetime, end_datetime = context.partition_time_window

    input_data = read_data_in_datetime_range(start_datetime, end_datetime)
    output_data = compute_events_from_raw_events(input_data)

    overwrite_data_in_datetime_range(start_datetime, end_datetime, output_data)
```
