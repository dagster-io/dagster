---
title: Partitioning Assets
description: Learn how to partition your data in Dagster.
sidebar_label: Partitioning Assets
sidebar_position: 30
---

In Dagster, partitioning is a powerful technique for managing large datasets, improving pipeline performance, and enabling incremental processing. This guide will help you understand how to implement data partitioning in your Dagster projects.

By the end of this guide, you'll have a comprehensive understanding of:

- Defining partitions for Dagster assets and jobs
- Establishing dependencies between partitioned assets
- Leveraging Dagster partitions with external systems like dbt

<details>
  <summary>Prerequisites</summary>

To follow the steps in this guide, you'll need:

- A basic understanding of Dagster and assets. See the [Quick Start](/tutorial/quick-start) tutorial for an overview.
- Basic understanding of data processing pipelines
- Python 3.7 or later installed
- Dagster library installed (`pip install dagster`)

</details>

## Define partitioned assets

There are several ways to partition your data in Dagster:

- [Time-based partitioning](#define-time-partitioned-assets), for processing data in specific time intervals
- [Static partitioning](#define-partitions-with-predefined-categories), for dividing data based on predefined categories
- [Dynamic partitioning](#define-partitions-with-dynamic-categories), for creating partitions based on runtime information
- [Two-dimensional partitioning](#define-two-dimensional-partitions), for partitioning data along two different axes simultaneously

### Define time-partitioned assets

A common use case for partitioning is to process data that divides into time intervals, such as daily logs or monthly reports. Here's how to implement time-based partitioning in Dagster:

<CodeExample filePath="guides/data-modeling/partitioning/time_based_partitioning.py" language="python" title="Time-based partitioning" />

In this example:

- We defined `daily_partitions` using `DailyPartitionsDefinition` with a start date of "2024-01-01". This will create a range of partitions from "2024-01-01" to the day before the current time.
- The `daily_sales_data` asset is defined with this partitioning scheme.
- The `daily_sales_summary` asset depends on `daily_sales_data` and also uses the same partitioning scheme.
- The schedule `daily_sales_schedule` runs the job daily at 1:00 AM which partitions the data for the previous day.

### Define partitions with predefined categories

Static partitioning is useful when you have predefined categories for your data. For instance, you might want to process data separately for different regions or product lines:

<CodeExample filePath="guides/data-modeling/partitioning/static_partitioning.py" language="python" title="Static partitioning" />

This example demonstrates how to create static partitions for different regions. The `regional_sales` asset uses these partitions to process sales data for each region independently.

### Define partitions with dynamic categories

Dynamic partitioning allows you to create partitions based on runtime information. This is useful when the partitions aren't known in advance:

<CodeExample filePath="guides/data-modeling/partitioning/dynamic_partitioning.py" language="python" title="Dynamic partitioning" />

In this example, we create dynamic partitions based on customer IDs. The `customer_data` asset processes data for each customer separately, with the partitions determined at runtime.

### Define two-dimensional partitions

Two-dimensional partitioning allows you to partition your data along two different axes simultaneously. This is useful when you need to process data that can be categorized in multiple ways. Here's an example of how to implement two-dimensional partitioning in Dagster:

<CodeExample filePath="guides/data-modeling/partitioning/two_dimensional_partitioning.py" language="python" title="Two-dimensional partitioning" />

In this example, we define a two-dimensional partition for processing sales data by both region and product category. The `sales_data` asset is configured to use these partitions, allowing you to materialize data for specific combinations of regions and product categories.

This approach is particularly useful when you need to analyze or process data across multiple dimensions, such as:

- Analyzing sales performance by both region and product category
- Processing user engagement data by both user segment and feature
- Generating reports for different departments across various time periods

By using two-dimensional partitioning, you can easily select and process specific subsets of your data, improving both the flexibility and efficiency of your data pipeline.

## Define dependencies between partitioned assets

### Connect Time-based Partitions

Partitioned assets in Dagster can have dependencies on other partitioned assets. This allows you to create complex data pipelines where the output of one partitioned asset feeds into another. Here's how it works:

- A downstream asset can depend on one or more partitions of an upstream asset
- The partitioning schemes don't need to be identical, but they should be compatible

Let's look at an example to illustrate this concept:

<CodeExample filePath="guides/data-modeling/partitioning/partitioned_dependencies.py" language="python" title="Partitioned asset dependencies" />

In this example:

1. We have a `daily_sales` asset partitioned by day
2. The `monthly_report` asset depends on the `daily_sales` asset
3. Each partition of `monthly_report` (a month) depends on multiple partitions of `daily_sales` (the days in that month)

This setup allows you to process daily data and then aggregate it into monthly reports, all while maintaining the benefits of partitioning.

### Connect Time-based and Static Partitions

Combining time-based and static partitions allows you to analyze data across both temporal and categorical dimensions. This is particularly useful for scenarios like regional time series analysis. Here's an example:

<CodeExample filePath="guides/data-modeling/partitioning/time_static_partitioning.py" language="python" title="Time-based and static partitioning" />

In this example:

1. We define a `daily_regional_sales` asset partitioned by both date and region.
2. The `monthly_regional_report` asset depends on `daily_regional_sales`.
3. Each partition of `monthly_regional_report` (a combination of month and region) depends on multiple partitions of `daily_regional_sales` (the days in that month for the specific region).

This setup enables you to:

- Process daily sales data for each region independently
- Generate monthly reports for each region based on the daily data
- Analyze trends and patterns across both time and geographical dimensions

By connecting time-based and static partitions, you create a flexible system that can handle complex analytical requirements while maintaining the benefits of partitioned data processing.

### Connect Time-based and Dynamic Partitions

TODO

### Connect Time-based partitions to un-partitioned assets

TODO

## Integrating Dagster Partitions with External Systems: Incremental Models and dbt

TODO

## Next steps

- Go deeper into [Understanding Partitioning](/concepts/understanding-partitioning)
