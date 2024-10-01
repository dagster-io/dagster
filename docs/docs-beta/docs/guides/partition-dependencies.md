---
title: Defining dependencies between partitioned assets
description: Learn how to define dependencies between partitioned and unpartitioned assets in Dagster.
sidebar_label: Partition dependencies
sidebar_position: 31
---

Now that you've seen how to model partitioned assets in different ways, you may want to define dependencies between the partitioned assets, or even between unpartitioned assets.

Partitioned assets in Dagster can have dependencies on other partitioned assets, allowing you to create complex data pipelines where the output of one partitioned asset feeds into another. Here's how it works:

- A downstream asset can depend on one or more partitions of an upstream asset
- The partitioning schemes don't need to be identical, but they should be compatible

---

<details>
<summary>Prerequisites</summary>

To follow the steps in this guide, you'll need:

- Familiarity with [Assets](/guides/data-assets)
- Familiarity with [Partitions](/guides/partitioning)

</details>

## Dependencies between different time-based partitions \{#different-time-dependencies}

The following example creates two partitions: `daily_sales_data` and `daily_sales_summary`, which can be executed at the same time in a single schedule.

<details>
<summary>Show example</summary>

<CodeExample filePath="guides/data-modeling/partitioning/time_based_partitioning.py" language="python" />

</details>

However, sometimes you might want to define dependencies between different time-based partitions. For example, you might want to aggregate daily data into a weekly report.

Consider the following example:

<CodeExample filePath="guides/data-modeling/partitioning/time_based_partition_dependencies.py" language="python" />

In this example:

- We have a `daily_sales_data` asset partitioned by day, which will be executed daily.
- The `weekly_sales_summary` asset depends on the `daily_sales_data` asset, which will be executed weekly.

  - In this asset, the weekly partition depends on all its parent partitions (all seven days of the week). We use `context.asset_partition_key_range_for_input("daily_sales_data")` to get a range of partition keys, which includes the start and end of the week.

- To automate the execution of these assets:

  - First, we specify `automation_condition=AutomationCondition.eager()` to the `weekly_sales_summary` asset. This ensures it runs weekly after all seven daily partitions of `daily_sales_data` are up-to-date.
  - Second, we specify `automation_condition=AutomationCondition.cron(cron_schedule="0 1 * * *")` to the `daily_sales_data` asset. This ensures it runs daily.

Note: In a simpler example above, we manually set up a daily schedule for asset execution. For more complex dependency logic, it's recommended to use automation conditions instead of schedules. Automation conditions specify when an asset should run, which allows you to define execution criteria without custom scheduling logic. For more details, see [Declarative Automation](/concepts/automation/declarative-automation).

## Dependencies between time-based partitions and un-partitioned assets

TODO

## Dependencies between time-based and static partitions

Combining time-based and static partitions allows you to analyze data across both temporal and categorical dimensions. This is particularly useful for scenarios like regional time series analysis.

{/* TODO */}

## Dependencies between time-based and dynamic partitions

{/* TODO */}

## Dependencies between time-based partitions and un-partitioned assets

{/* TODO */}

## Integrating Dagster partitions with external systems: incremental models and dbt

{/* TODO */}

## Next steps

- Go deeper into [Understanding Partitioning](#)
