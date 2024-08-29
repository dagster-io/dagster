---
title: How to Partition Your Data
description: Learn how to partition your data in Dagster.
sidebar_label: Partitioning pipelines
sidebar_position: 30
---

In Dagster, partitioning is a powerful technique for managing large datasets and improving pipeline performance. This guide will help you understand how to implement data partitioning in your Dagster projects.

There are several ways to partition your data in Dagster:

- Time-based partitioning, for processing data in specific time intervals
- Static partitioning, for dividing data based on predefined categories
- Dynamic partitioning, for creating partitions based on runtime information

This guide walks through these methods and demonstrates how to use them effectively in your data pipelines.

## What you'll learn

- How to define partitions for your Dagster assets and jobs
- Techniques for implementing time-based and static partitions
- How to use partition keys to selectively run parts of your pipeline
- Best practices for working with partitioned data in Dagster

<details>
  <summary>Prerequisites</summary>

To follow the steps in this guide, you'll need:

- A basic understanding of Dagster and assets. See the [Quick Start](/tutorial/quick-start) tutorial for an overview.
- Basic understanding of data processing pipelines
- Python 3.7 or later installed
- Dagster library installed (`pip install dagster`)

</details>

## Partition based on time intervals

Time-based partitioning is a common approach for processing data that naturally divides into time intervals, such as daily logs or monthly reports. Here's how to implement time-based partitioning in Dagster:

<CodeExample filePath="guides/data-modeling/partitioning/time_based_partitioning.py" language="python" title="Time-based partitioning" />

In this example, we define a daily partition for processing log data. The `daily_logs` asset is configured to use these partitions, allowing you to materialize data for specific dates or date ranges.

## Partition based on static categories

Static partitioning is useful when you have predefined categories for your data. For instance, you might want to process data separately for different regions or product lines:

<CodeExample filePath="guides/data-modeling/partitioning/static_partitioning.py" language="python" title="Static partitioning" />

This example demonstrates how to create static partitions for different regions. The `regional_sales` asset uses these partitions to process sales data for each region independently.

## Partition based on dynamic categories

Dynamic partitioning allows you to create partitions based on runtime information. This is useful when the partitions aren't known in advance:

<CodeExample filePath="guides/data-modeling/partitioning/dynamic_partitioning.py" language="python" title="Dynamic partitioning" />

In this example, we create dynamic partitions based on customer IDs. The `customer_data` asset processes data for each customer separately, with the partitions determined at runtime.

## Define two-dimensional partitioning

Two-dimensional partitioning allows you to partition your data along two different axes simultaneously. This is useful when you need to process data that can be categorized in multiple ways. Here's an example of how to implement two-dimensional partitioning in Dagster:

<CodeExample filePath="guides/data-modeling/partitioning/two_dimensional_partitioning.py" language="python" title="Two-dimensional partitioning" />

In this example, we define a two-dimensional partition for processing sales data by both region and product category. The `sales_data` asset is configured to use these partitions, allowing you to materialize data for specific combinations of regions and product categories.

This approach is particularly useful when you need to analyze or process data across multiple dimensions, such as:

- Analyzing sales performance by both region and product category
- Processing user engagement data by both user segment and feature
- Generating reports for different departments across various time periods

By using two-dimensional partitioning, you can easily select and process specific subsets of your data, improving both the flexibility and efficiency of your data pipeline.

## Define Dependencies Between Partitioned Assets

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

### Connect Time-based Partitions: Connecting Daily and Monthly Assets

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

User Cohort Analysis Over Time

### Connect Static Partitions

<!-- ### Interconnecting Dynamic Partitions: Customer Segment and Behavior Analysis

Dynamic partitions can be interconnected to create complex, flexible data processing pipelines. This is particularly useful when dealing with data that has multiple, interrelated dynamic aspects. Let's look at an example that combines customer segmentation with behavior analysis:

<CodeExample filePath="guides/data-modeling/partitioning/dynamic_partitioned_dependencies.py" language="python" title="Interconnected dynamic partitions" />

In this example:

1. We define two dynamically partitioned assets: `customer_segments` and `customer_behavior`.
2. The `customer_segments` asset creates partitions based on customer attributes that may change over time.
3. The `customer_behavior` asset depends on `customer_segments` and analyzes behavior patterns within each segment.
4. The partitioning for both assets is determined at runtime, allowing for flexible and adaptive data processing.

This setup allows for sophisticated analysis where:

- Customer segments can be dynamically created or updated based on changing data.
- Behavior analysis can be performed specifically for each dynamically determined segment.
- The pipeline can adapt to new segments or changing customer attributes without requiring code changes.

By interconnecting dynamic partitions in this way, you can create data pipelines that are both powerful and flexible, capable of handling complex, evolving datasets and business requirements. -->

## Next steps

- Go deeper into [Understanding Partitioning](/concepts/understanding-partitioning)
