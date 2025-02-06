---
title: Partitioning assets
description: Learn how to partition your data in Dagster.
sidebar_position: 100
---

In Dagster, partitioning is a powerful technique for managing large datasets, improving pipeline performance, and enabling incremental processing. This guide will help you understand how to implement data partitioning in your Dagster projects.

There are several ways to partition your data in Dagster:

- [Time-based partitioning](#time-based), for processing data in specific time intervals
- [Static partitioning](#static-partitions), for dividing data based on predefined categories
- [Two-dimensional partitioning](#two-dimensional-partitions), for partitioning data along two different axes simultaneously
- [Dynamic partitioning](#dynamic-partitions), for creating partitions based on runtime information

:::note

We recommend limiting the number of partitions for each asset to 25,000 or fewer. Assets with partition counts exceeding this limit will likely have slower load times in the UI.

:::

## Time-based partitions \{#time-based}

A common use case for partitioning is to process data that can be divided into time intervals, such as daily logs or monthly reports.

<CodeExample path="docs_beta_snippets/docs_beta_snippets/guides/data-modeling/partitioning/time_based_partitioning.py" language="python" />

## Partitions with predefined categories \{#static-partitions}

Sometimes you have a set of predefined categories for your data. For instance, you might want to process data separately for different regions.

<CodeExample path="docs_beta_snippets/docs_beta_snippets/guides/data-modeling/partitioning/static_partitioning.py" language="python" />

{/* TODO: Link to Backfill page to explain how to backfill regional sales data */}

## Two-dimensional partitions \{#two-dimensional-partitions}

Two-dimensional partitioning allows you to partition data along two different axes simultaneously. This is useful when you need to process data that can be categorized in multiple ways. For example:

<CodeExample path="docs_beta_snippets/docs_beta_snippets/guides/data-modeling/partitioning/two_dimensional_partitioning.py" language="python" />

In this example:

- Using `MultiPartitionsDefinition`, the `two_dimensional_partitions` is defined with two dimensions: `date` and `region`
- The partition key would be: `2024-08-01|us`
- The `daily_regional_sales_data` and `daily_regional_sales_summary` assets are defined with the same two-dimensional partitioning scheme
- The `daily_regional_sales_schedule` runs daily at 1:00 AM, processing the previous day's data for all regions. It uses `MultiPartitionKey` to specify partition keys for both date and region dimensions, resulting in three runs per day, one for each region.

## Partitions with dynamic categories \{#dynamic-partitions}

Sometimes you don't know the partitions in advance. For example, you might want to process new regions that are added in your system. In these cases, you can use dynamic partitioning to create partitions based on runtime information.

Consider this example:

<CodeExample path="docs_beta_snippets/docs_beta_snippets/guides/data-modeling/partitioning/dynamic_partitioning.py" language="python" title="Dynamic partitioning" />

In this example:

- Because the partition values are unknown in advance, `DynamicPartitionsDefinition` is used to define `region_partitions`
- When triggered, the `all_regions_sensor` will dynamically add all regions to the partition set. Once it kicks off runs, it will dynamically kick off runs for all regions. In this example, that would be six times; one for each region.

## Materializing partitioned assets

When you materialize a partitioned asset, you choose which partitions to materialize and Dagster will launch a run for each partition. 

:::note

If you choose more than one partition, the [Dagster daemon](/guides/deploy/execution/dagster-daemon) needs to be running to queue the multiple runs.

:::

The following image shows the **Launch runs** dialog on an asset's **Details** page, where you'll be prompted to select a partition to materialize:

![Rematerialize partition](/images/guides/build/partitions-and-backfills/rematerialize-partition.png)

After a partition has been successfully materialized, it will display as green in the partitions bar:

![Successfully materialized partition](/images/guides/build/partitions-and-backfills/materialized-partitioned-asset.png)

## Viewing materializations by partition

To view materializations by partition for a specific asset, navigate to the **Activity** tab of the asset's **Details** page:

![Asset activity section of asset details page](/images/guides/build/partitions-and-backfills/materialized-partitioned-asset-activity.png)