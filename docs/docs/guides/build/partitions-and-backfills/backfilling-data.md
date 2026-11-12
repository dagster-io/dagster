---
title: Backfilling data
description: Backfilling is the process of running partitions for assets that either don't exist or updating existing records. Dagster supports data backfills for each partition or subsets of partitions.
sidebar_position: 300
---

Backfilling is the process of running partitions for assets that either don't exist or updating existing records. Dagster supports backfills for each partition or a subset of partitions.

After defining a [partition](/guides/build/partitions-and-backfills/partitioning-assets), you can launch a backfill that will submit runs to fill in multiple partitions at the same time.

Backfills are common when setting up a pipeline for the first time. The assets you want to materialize might have historical data that needs to be materialized to get the assets up to date. Another common reason to run a backfill is when you've changed the logic for an asset and need to update historical data with the new logic.

## Launching backfills for partitioned assets

To launch backfills for a partitioned asset, click the **Materialize** button on either the **Asset details** or the **Global asset lineage** page. The backfill modal will display.

Backfills can also be launched for a selection of partitioned assets as long as the most upstream assets share the same partitioning. For example: All partitions use a `DailyPartitionsDefinition`.

![Backfills launch modal](/images/guides/build/partitions-and-backfills/asset-backfill-partition-selection-modal.png)

:::note

The "Launch as..." toggle shown in the screenshot above (for choosing between single run and multiple runs) was removed from the UI in Dagster 1.5. Single-run backfills are now configured in code using `backfill_policy`. See [Launching single-run backfills using backfill policies](#launching-single-run-backfills-using-backfill-policies) below.

:::

To observe the progress of an asset backfill, navigate to the **Runs details** page for the run. This page can be accessed by clicking **Runs tab**, then clicking the ID of the run. To see all runs, including runs launched by a backfill, check the **Show runs within backfills** box:

![Asset backfill details page](/images/guides/build/partitions-and-backfills/asset-backfill-details-page.png)

## Launching single-run backfills using backfill policies


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

  - [`partition_time_window`](/api/dagster/execution#dagster.OpExecutionContext.partition_time_window)
  - [`partition_key_range`](/api/dagster/execution#dagster.OpExecutionContext.partition_key_range)
  - [`partition_keys`](/api/dagster/execution#dagster.OpExecutionContext.partition_keys)

  Which property to use depends on whether it's most convenient for you to operate on start/end datetime objects, start/end partition keys, or a list of partition keys.

<CodeExample path="docs_snippets/docs_snippets/guides/build/partitions_backfills/backfills/single_run_backfill_asset.py" startAfter="start_marker" endBefore="end_marker" title="src/<project_name>/defs/assets.py" />

## Handling code locations that fail to load

Before processing each iteration of an asset backfill, Dagster validates the backfill targets against the current asset graph. If an asset or partition targeted by the backfill can't be found - for example, because the code location it belongs to is temporarily failing to load - the backfill will fail with a `DagsterAssetBackfillDataLoadError` and any queued runs will be canceled.

This can happen even when your definitions haven't actually changed. For example, a transient error - such as an intermittent gRPC deserialization failure while fetching data from a code server ([GitHub issue #34338](https://github.com/dagster-io/dagster/issues/34338)) - can make the assets in a code location temporarily invisible to the backfill validation step, which would otherwise fail the backfill.

To make asset backfills resilient to this, set the `DAGSTER_BACKFILL_RETRY_DEFINITION_CHANGED_ERROR` environment variable on the Dagster daemon:

```bash
export DAGSTER_BACKFILL_RETRY_DEFINITION_CHANGED_ERROR=1
```

When this variable is set and at least one code location is failing to load, the daemon won't fail the backfill when validation finds a missing asset or partition. Instead, it will log a warning and skip the current backfill iteration. The backfill will remain active and will resume once the code location loads successfully.

Note that this variable:

- Only applies to asset backfills, and only when the missing asset or partition coincides with a code location that is failing to load. If all code locations load successfully and the definition has actually changed - for example, an asset was removed or its partitions changed - the backfill will still fail.
- Doesn't fix the underlying error that caused the code location to fail to load. It only keeps the backfill from being canceled while the location is temporarily unavailable.
- Is opt-in. Unless it's set, backfills behave as described above and fail immediately on a validation error.

