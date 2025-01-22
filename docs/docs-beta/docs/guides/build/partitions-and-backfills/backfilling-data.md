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

## Launching backfills using the Python API (experimental)

You can also launch backfills using the Python API from a schedule or sensor. To do this, you need to construct a `RunRequest` object that optionally specifies the partitions you want to backfill.

```python file=/concepts/partitions_schedules_sensors/backfills/backfill_asset_from_asset_partitions.py
from dagster import (
    AssetIn,
    AssetKey,
    RunRequest,
    StaticPartitionMapping,
    StaticPartitionsDefinition,
    asset,
    schedule,
)

partitions_a = StaticPartitionsDefinition(["foo_a"])

partitions_b = StaticPartitionsDefinition(["foo_b"])


@asset(partitions_def=partitions_a)
def asset_a():
    pass


@asset(
    partitions_def=partitions_b,
    ins={"asset_a": AssetIn(partition_mapping=StaticPartitionMapping({"foo_a": "foo_b"}))},
)
def asset_b(asset_a):
    pass


asset_selection = [
    AssetKey("asset_a"),
    AssetKey("asset_b"),
]

partition_keys = partitions_a.get_partition_keys()


@schedule(target=asset_selection, cron_schedule="* * * * *")
def launch_backfill_with_multiple_assets_selected(context):
    return RunRequest.from_asset_partitions(
        # asset_selection=asset_selection,  # implied by the target argument
        partition_names=partition_keys,
        tags={"custom_tag_key": "custom_tag_value"},
        all_partitions=False,
    )
```

Alternatively, you can specify the set of partitions for each asset key to backfill:

```python file=/concepts/partitions_schedules_sensors/backfills/backfill_asset_from_partitions_by_assets.py
from dagster import (
    AssetKey,
    BackfillPolicy,
    DailyPartitionsDefinition,
    DefaultSensorStatus,
    RunRequest,
    asset,
    sensor,
)

daily_partitions_def = DailyPartitionsDefinition("2023-01-01")


@asset(
    partitions_def=daily_partitions_def,
    backfill_policy=BackfillPolicy.single_run(),
)
def asset_with_single_run_backfill_policy():
    pass


partitions = ["2023-01-01", "2023-01-02", "2023-01-03", "2023-01-04", "2023-01-05"]


@sensor(
    target=AssetKey("asset_with_single_run_backfill_policy"),
    minimum_interval_seconds=5,
    default_status=DefaultSensorStatus.RUNNING,
)
def launch_backfill_with_single_run_backfill_policy(context):
    yield RunRequest.from_partitions_by_assets(
        partitions_by_assets={asset_with_single_run_backfill_policy.key: set(partitions)},
        tags={},  # optional
        title=None,  # optional
        description=None,  # optional
    )
```
