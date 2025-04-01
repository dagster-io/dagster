---
title: Defining dependencies between partitioned assets
description: Learn how to define dependencies between partitioned and unpartitioned assets in Dagster.
sidebar_label: Partitioning dependencies
sidebar_position: 200
---

Now that you've seen how to model partitioned assets in different ways, you may want to define dependencies between the partitioned assets, or even between unpartitioned assets.

Partitioned assets in Dagster can have dependencies on other partitioned assets, allowing you to create complex data pipelines where the output of one partitioned asset feeds into another. Here's how it works:

- A downstream asset can depend on one or more partitions of an upstream asset
- The partitioning schemes don't need to be identical, but they should be compatible

## Default partition dependency rules

A few rules govern default partition-to-partition dependencies:

- When the upstream asset and downstream asset have the same <PyObject section="partitions" module="dagster" object="PartitionsDefinition" />, each partition in the downstream asset will depend on the same partition in the upstream asset.
- When the upstream asset and downstream asset are both [time window-partitioned](partitioning-assets#time-based), each partition in the downstream asset will depend on all partitions in the upstream asset that intersect its time window.

For example, if an asset with a <PyObject section="partitions" module="dagster" object="DailyPartitionsDefinition" /> depends on an asset with an <PyObject section="partitions" module="dagster" object="HourlyPartitionsDefinition" />, then partition `2024-04-12` of the daily asset would depend on 24 partitions of the hourly asset: `2024-04-12-00:00` through `2024-04-12-23:00`.

## Overriding default dependency rules

Default partition dependency rules can be overridden by providing a <PyObject section="partitions" module="dagster" object="PartitionMapping" /> when specifying a dependency on an asset. How this is accomplished depends on the type of dependency the asset has.

### Basic asset dependencies

To override partition dependency rules for basic asset dependencies, you can use <PyObject section="assets" module="dagster" object="AssetDep" /> to specify the partition dependency on an upstream asset:

<CodeExample path="docs_snippets/docs_snippets/concepts/partitions_schedules_sensors/partitioned_asset_mappings.py" />

### Managed-loading asset dependencies

To override partition dependency rules for managed-loading asset dependencies, you can use a <PyObject section="partitions" module="dagster" object="PartitionMapping" /> to specify that each partition of an asset should depend on a partition in an upstream asset.

In the following code, we use a <PyObject section="partitions" module="dagster" object="TimeWindowPartitionMapping" /> to specify that each partition of a daily-partitioned asset should depend on the prior day's partition in an upstream asset:

<CodeExample path="docs_snippets/docs_snippets/concepts/partitions_schedules_sensors/partition_mapping.py" />

For a list of available `PartitionMappings`, see the [API docs](/api/python-api/partitions#dagster.PartitionMapping). Note that custom `PartitionMapping` and overriding `PartitionMapping` outside of Dagster is not currently supported.

## Examples

### Dependencies between different time-based partitions \{#different-time-dependencies}

The following example creates two partitions: `daily_sales_data` and `daily_sales_summary`, which can be executed at the same time in a single schedule.

<details>
<summary>Show example</summary>

<CodeExample path="docs_snippets/docs_snippets/guides/data-modeling/partitioning/time_based_partitioning.py" language="python" />

</details>

However, sometimes you might want to define dependencies between different time-based partitions. For example, you might want to aggregate daily data into a weekly report.

Consider the following example:

<CodeExample path="docs_snippets/docs_snippets/guides/data-modeling/partitioning/time_based_partition_dependencies.py" language="python" />

In this example:

- We have a `daily_sales_data` asset partitioned by day, which will be executed daily.
- The `weekly_sales_summary` asset depends on the `daily_sales_data` asset, which will be executed weekly.

  - In this asset, the weekly partition depends on all its parent partitions (all seven days of the week). We use `context.asset_partition_key_range_for_input("daily_sales_data")` to get a range of partition keys, which includes the start and end of the week.

- To automate the execution of these assets:

  - First, we specify `automation_condition=AutomationCondition.eager()` to the `weekly_sales_summary` asset. This ensures it runs weekly after all seven daily partitions of `daily_sales_data` are up-to-date.
  - Second, we specify `automation_condition=AutomationCondition.cron(cron_schedule="0 1 * * *")` to the `daily_sales_data` asset. This ensures it runs daily.


:::tip

We recommend using [automation conditions](/guides/automate/declarative-automation/) instead of [schedules](/guides/automate/schedules) for code with complex dependency logic, such as the example above. Automation conditions specify when an asset should run, which allows you to define execution criteria without needing to add custom scheduling logic.

:::


{/* ## Dependencies between time-based partitions and un-partitioned assets */}

{/* TODO */}

{/* ## Dependencies between time-based and static partitions */}

{/* Combining time-based and static partitions allows you to analyze data across both temporal and categorical dimensions. This is particularly useful for scenarios like regional time series analysis. */}

{/* TODO */}

{/* ## Dependencies between time-based and dynamic partitions */}

{/* TODO */}

{/* ## Dependencies between time-based partitions and un-partitioned assets */}

{/* TODO */}

{/* ## Integrating Dagster partitions with external systems: incremental models and dbt */}

{/* TODO */}
