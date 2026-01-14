---
title: Partitions vs config
description: Comparing Dagster's partitions with run configuration for parameterizing pipelines.
last_update:
  author: Dennis Hume
sidebar_custom_props:
  logo: images/dagster-primary-mark.svg
---

In this example, we'll explore two different approaches to parameterize Dagster pipelines. When you need to process data for different segments (like customers, regions, or dates), you can choose between Dagster's [partitions](/guides/build/partitions-and-backfills/partitioning-assets) or [run configuration](/guides/operate/configuration/run-configuration). Each approach has distinct trade-offs in terms of tracking, observability, and workflow.

## Problem: Processing data for multiple customers

Imagine you need to process data for multiple customers, where each customer's data should be processed independently. You want to be able to run the pipeline for specific customers and potentially reprocess historical data when needed.

The key question is: Should you use partitions to create a segment for each customer, or should you use config to pass the customer ID as a parameter?

### Solution 1: Using partitions

[Partitions](/guides/build/partitions-and-backfills/partitioning-assets) divide your data into discrete segments. Each customer becomes a partition, giving you full visibility into which customers have been processed and the ability to backfill specific customers.

<CodeExample
  path="docs_projects/project_mini/src/project_mini/defs/partitions_vs_config/with_partitions.py"
  language="python"
  title="src/project_mini/defs/partitions_vs_config/with_partitions.py"
/>

|                              | **Partitions approach**                              |
| ---------------------------- | ---------------------------------------------------- |
| **Materialization tracking** | Per-customer history visible in UI                   |
| **Backfilling**              | Built-in support for reprocessing specific customers |
| **Scheduling**               | Native support for processing all partitions         |
| **UI experience**            | Partition status bar shows processing state          |
| **Setup complexity**         | Requires defining partition set upfront              |

### Solution 2: Using config

[Run configuration](/guides/operate/configuration/run-configuration) passes the customer ID as a parameter at runtime. This approach is simpler to set up but doesn't track which customers have been processed.

<CodeExample
  path="docs_projects/project_mini/src/project_mini/defs/partitions_vs_config/with_config.py"
  language="python"
  title="src/project_mini/defs/partitions_vs_config/with_config.py"
/>

|                              | **Config approach**                           |
| ---------------------------- | --------------------------------------------- |
| **Materialization tracking** | Single asset history (not per-customer)       |
| **Backfilling**              | Manual re-runs required                       |
| **Scheduling**               | Requires custom logic to iterate customers    |
| **UI experience**            | Specify customer in Launchpad before each run |
| **Setup complexity**         | Simple config class, no partition management  |

## When to use each approach

The choice between partitions and config depends on your specific requirements:

**Use partitions when:**

- Your data naturally segments into discrete categories
- You need to track materialization status per segment
- Backfilling specific segments is a common operation
- You want to schedule processing for all segments automatically
- You need visibility into which segments are up-to-date vs stale

**Use config when:**

- Processing is infrequent or ad-hoc
- Parameters are dynamic or come from an unbounded set
- You don't need per-parameter tracking
- A single materialization history is sufficient
- You want simple parameterization without partition overhead

## Hybrid approach

You can also combine both approaches: use partitions for the primary segmentation (e.g., by customer) and config for additional runtime parameters (e.g., processing options).

<CodeExample
  path="docs_projects/project_mini/src/project_mini/defs/partitions_vs_config/with_partitions_and_config.py"
  language="python"
  title="src/project_mini/defs/partitions_vs_config/with_partitions_and_config.py"
/>

This gives you the benefits of partition tracking while maintaining flexibility for runtime parameters.
