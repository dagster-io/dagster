---
title: Partitioning assets
description: Learn how to partition your data in Dagster.
sidebar_label: Partition data
sidebar_position: 30
---

In Dagster, partitioning is a powerful technique for managing large datasets, improving pipeline performance, and enabling incremental processing. This guide will help you understand how to implement data partitioning in your Dagster projects.

## What you'll learn

- How to define partitions for Dagster assets and jobs
- How to establish dependencies between partitioned assets
- How to leverage Dagster partitions with external systems like dbt

---

<details>
  <summary>Prerequisites</summary>

To follow the steps in this guide, you'll need:

- A basic understanding of Dagster and assets. See the [Quick Start](/getting-started/quickstart) tutorial for an overview.

</details>

## Define partitioned assets

There are several ways to partition your data in Dagster:

- [Time-based partitioning](#define-time-partitioned-assets), for processing data in specific time intervals
- [Static partitioning](#define-partitions-with-predefined-categories), for dividing data based on predefined categories
- [Two-dimensional partitioning](#define-two-dimensional-partitions), for partitioning data along two different axes simultaneously
- [Dynamic partitioning](#define-partitions-with-dynamic-categories), for creating partitions based on runtime information

### Define time-partitioned assets

A common use case for partitioning is to process data that can be divided into time intervals, such as daily logs or monthly reports. Here's how to implement time-based partitioning in Dagster:

<CodeExample filePath="guides/data-modeling/partitioning/time_based_partitioning.py" language="python" title="Time-based partitioning" />

In this example:

- We defined `daily_partitions` using `DailyPartitionsDefinition` with a start date of "2024-01-01". This will create a range of partitions from "2024-01-01" to the day before the current time.
- The `daily_sales_data` asset is defined with this partitioning scheme.
- The `daily_sales_summary` asset depends on `daily_sales_data` and also uses the same partitioning scheme.
- The schedule `daily_sales_schedule` runs the job daily at 1:00 AM UTC and processes the previous day's data.

### Define partitions with predefined categories

Sometimes you have a set of predefined categories for your data. For instance, you might want to process data separately for different regions.

<CodeExample filePath="guides/data-modeling/partitioning/static_partitioning.py" language="python" title="Static partitioning" />

In this example:

- We defined `region_partitions` using `StaticPartitionsDefinition` with a list of regions.
- The `regional_sales_data` and `daily_sales_summary` are defined with the same partitioning scheme.

{/* TODO: Link to Backfill page to explain how to backfill regional sales data */}

### Define two-dimensional partitions

Two-dimensional partitioning allows you to partition your data along two different axes simultaneously. This is useful when you need to process data that can be categorized in multiple ways. Here's an example of how to implement two-dimensional partitioning in Dagster:

<CodeExample filePath="guides/data-modeling/partitioning/two_dimensional_partitioning.py" language="python" title="Two-dimensional partitioning" />

In this example:

- We defined `two_dimensional_partitions` using `MultiPartitionsDefinition` with two dimensions: `date` and `region`.
- The partition key would be: `2024-08-01|us`.
- The `daily_regional_sales_data` and `daily_regional_sales_summary` assets are defined with the same two-dimensional partitioning scheme.
- The `daily_regional_sales_schedule` runs daily at 1:00 AM, processing the previous day's data for all regions. It uses `MultiPartitionKey` to specify partition keys for both date and region dimensions, resulting in 3 runs per day (one for each region).

### Define partitions with dynamic categories

Sometimes you don't know the partitions in advance. For example, you might want to process regions that are added in your system. In such cases, you can use dynamic partitioning to create partitions based on runtime information.

<CodeExample filePath="guides/data-modeling/partitioning/dynamic_partitioning.py" language="python" title="Dynamic partitioning" />

In this example:

- We defined `region_partitions` using `DynamicPartitionsDefinition` without knowing the values in advance.
- The `all_regions_sensor` is a sensor that will dynamically add all regions to the partition set. Once it kicks off runs, it will dynamically kick off runs for all regions (in this example, 6 times; one for each region).

## Define dependencies between partitioned assets

Now that you've seen how to model partitioned assets in different ways, this section shows how to define dependencies between various partitioned assets, and between partitioned assets and un-partitioned assets.

Partitioned assets in Dagster can have dependencies on other partitioned assets. This allows you to create complex data pipelines where the output of one partitioned asset feeds into another. Here's how it works:

- A downstream asset can depend on one or more partitions of an upstream asset
- The partitioning schemes don't need to be identical, but they should be compatible

### Dependencies between different time-based partitions

In [Define time-partitioned assets](#define-time-partitioned-assets), we created two time-partitioned assets: `daily_sales_data` and `daily_sales_summary`, which can be executed at the same time in a single schedule.

However, sometimes you might want to define dependencies between different time-based partitions. For example, you might want to aggregate daily data into a weekly report.

In this case, we have a `weekly_sales_summary` asset that depends on the `daily_sales_data` asset. Here's how to set up dependencies between different time-based partitions:

<CodeExample filePath="guides/data-modeling/partitioning/time_based_partition_dependencies.py" language="python" title="Time-based partition dependencies" />

In this example:

- We have a `daily_sales_data` asset partitioned by day, which will be executed daily.
- The `weekly_sales_summary` asset depends on the `daily_sales_data` asset, which will be executed weekly.

  - In this asset, the weekly partition depends on all its parent partitions (all seven days of the week). We use `context.asset_partition_key_range_for_input("daily_sales_data")` to get a range of partition keys, which includes the start and end of the week.

- To automate the execution of these assets:

  - First, we specify `automation_condition=AutomationCondition.eager()` to the `weekly_sales_summary` asset. This ensures it runs weekly after all seven daily partitions of `daily_sales_data` are up-to-date.
  - Second, we specify `automation_condition=AutomationCondition.cron(cron_schedule="0 1 * * *")` to the `daily_sales_data` asset. This ensures it runs daily.

Note: In [a simpler example](#define-time-partitioned-assets) above, we manually set up a daily schedule for asset execution. For more complex dependency logic, it's recommended to use automation conditions instead of schedules. Automation conditions specify when an asset should run, which allows you to define execution criteria without custom scheduling logic. For more details, see [Declarative Automation](/concepts/automation/declarative-automation).

### Dependencies between time-based partitions and un-partitioned assets

TODO

### Dependencies between time-based and static partitions

Combining time-based and static partitions allows you to analyze data across both temporal and categorical dimensions. This is particularly useful for scenarios like regional time series analysis.

{/* TODO */}

### Dependencies between time-based and dynamic partitions

{/* TODO */}

### Dependencies between time-based partitions and un-partitioned assets

{/* TODO */}

## Integrating Dagster partitions with external systems: incremental models and dbt

{/* TODO */}

## Next steps

- Go deeper into [Understanding Partitioning](#)
