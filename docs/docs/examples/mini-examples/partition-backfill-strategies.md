---
title: Partition backfill strategies
description: Comparing backfill strategies for partitioned assets - one run per partition, batched runs, or single run.
last_update:
  author: Dennis Hume
sidebar_custom_props:
  logo: images/dagster-primary-mark.svg
---

In this example, we'll explore three different strategies for [backfilling](/guides/build/partitions-and-backfills/backfilling-data) partitioned assets. When you need to materialize multiple partitions (for initial setup or reprocessing), you can choose between Dagster's default one-run-per-partition approach, a batched approach, or a single-run approach using <PyObject section="partitions" module="dagster" object="BackfillPolicy" />. Each strategy has distinct trade-offs in terms of overhead, fault isolation, and resource utilization.

| Factor              | One per partition | Batched               | Single run     |
| ------------------- | ----------------- | --------------------- | -------------- |
| **Run overhead**    | High (N runs)     | Medium (N/batch runs) | Low (1 run)    |
| **Fault isolation** | Best              | Moderate              | None           |
| **Retry cost**      | 1 partition       | 1 batch               | All partitions |
| **Observability**   | Per partition     | Per batch             | Aggregate only |

## Problem: Backfilling 100 days of historical data

Imagine you need to backfill 100 days of historical event data. Each day's data needs to be processed and stored. Without optimization, this could mean launching 100 separate runs, each with its own overhead. But processing everything in one run means a single failure requires reprocessing all 100 days.

The key question is: How should you batch your partitions to balance overhead, fault isolation, and performance?

| Solution                                                                     | Best for                                                                                             |
| ---------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| [One run per partition (default)](#solution-1-one-run-per-partition-default) | Unreliable data sources, API rate limits, fine-grained retry capability, per-partition observability |
| [Batched runs](#solution-2-batched-runs)                                     | Reducing overhead while maintaining fault isolation, short processing times, initial backfills       |
| [Single run](#solution-3-single-run)                                         | Spark/Snowflake/Databricks, range-based queries, minimizing Dagster Cloud credits                    |

## Solution 1: One run per partition (default)

By default, Dagster launches one run per partition. This provides maximum observability and fault isolation—if one partition fails, others continue independently, and partitions are individually retried. For 100 partitions, this creates 100 separate runs, each with its own startup overhead. This approach is best when your data source is unreliable (API rate limits, transient failures), you need fine-grained retry capability for individual partitions, or per-partition observability is critical.

<CodeExample
  path="docs_projects/project_mini/src/project_mini/defs/partition_backfill_strategies/multi_run_backfill.py"
  language="python"
  title="src/project_mini/defs/partition_backfill_strategies/multi_run_backfill.py"
/>

## Solution 2: Batched runs

With <PyObject section="partitions" module="dagster" object="BackfillPolicy.multi_run"/>, Dagster groups partitions into batches. For example, with `max_partitions_per_run=10`, 100 partitions become 10 runs of 10 partitions each. This reduces overhead by 90% while maintaining moderate fault isolation—if one partition fails, only its batch of 10 needs to retry. This approach works well when you want to reduce overhead while maintaining some fault isolation, processing time per partition is short (seconds to a few minutes), or you're doing an initial backfill of many partitions.

<CodeExample
  path="docs_projects/project_mini/src/project_mini/defs/partition_backfill_strategies/batched_backfill.py"
  language="python"
  title="src/project_mini/defs/partition_backfill_strategies/batched_backfill.py"
/>

When using <PyObject section="partitions" module="dagster" object="BackfillPolicy.multi_run"/>, consider:

- **Overhead reduction**: Batch size of 10 reduces runs by 90%
- **Failure blast radius**: If one partition fails, the entire batch retries
- **Memory usage**: More partitions per run may require more memory
- **Processing model**: Sequential processing means larger batches take longer

**Recommended starting points:**

| Partition processing time | Suggested batch size |
| ------------------------- | -------------------- |
| Under 1 minute            | 20-50                |
| 1-5 minutes               | 10-20                |
| 5-15 minutes              | 5-10                 |
| Over 15 minutes           | 1-5 or single run    |

Adjust based on observed failure rates and infrastructure constraints. For more information on parallelization within batched runs, see [Parallelization within batched runs](#parallelization-within-batched-runs).

## Solution 3: Single run

With <PyObject section="partitions" module="dagster" object="BackfillPolicy.single_run"/>, Dagster processes all selected partitions in one run, eliminating per-run overhead entirely. For 100 partitions, this creates just 1 run. However, a failure requires retrying all partitions together. This approach is ideal when you're using a parallel-processing engine (Spark, Snowflake, Databricks), your queries naturally operate on date ranges, or you want to minimize Dagster Cloud credit consumption.

<CodeExample
  path="docs_projects/project_mini/src/project_mini/defs/partition_backfill_strategies/single_run_backfill.py"
  language="python"
  title="src/project_mini/defs/partition_backfill_strategies/single_run_backfill.py"
/>

| Scenario                                   | Recommended strategy        |
| ------------------------------------------ | --------------------------- |
| API with rate limits or transient failures | One per partition           |
| Short processing time, reliable source     | Batched (10-50 per run)     |
| Spark/Snowflake with range queries         | Single run                  |
| Cost optimization in Dagster Cloud         | Single run or large batches |
| Initial backfill of 1000+ partitions       | Batched (50-100 per run)    |

## Parallelization within batched runs

When using <PyObject section="partitions" module="dagster" object="BackfillPolicy.multi_run"/>, you get multiple partitions in a single run. Here are different ways to parallelize processing within that run.

| Strategy     | Best for        | Max concurrency     | Overhead | Complexity |
| ------------ | --------------- | ------------------- | -------- | ---------- |
| Batch query  | SQL databases   | N/A (single query)  | Very low | Very low   |
| Thread pool  | I/O-bound tasks | 10-100 threads      | Low      | Low        |
| Process pool | CPU-bound tasks | Number of CPU cores | Medium   | Low        |

## Strategy 1: Batch query (fastest for databases)

Process all partitions in a single database query:

<CodeExample
  path="docs_projects/project_mini/src/project_mini/defs/partition_backfill_strategies/parallel_batch_query.py"
  language="python"
  title="src/project_mini/defs/partition_backfill_strategies/parallel_batch_query.py"
/>

**Best for:** SQL databases, REST APIs with batch endpoints

## Strategy 2: Thread pool (I/O-bound operations)

Use threads for parallel I/O operations:

<CodeExample
  path="docs_projects/project_mini/src/project_mini/defs/partition_backfill_strategies/parallel_threadpool.py"
  language="python"
  title="src/project_mini/defs/partition_backfill_strategies/parallel_threadpool.py"
/>

**Best for:** HTTP requests, file I/O, database queries

**Parallelism:** Limited by `max_workers` (5 concurrent in this example)

## Strategy 3: Process pool (CPU-bound operations)

Use processes for parallel CPU-intensive work:

<CodeExample
  path="docs_projects/project_mini/src/project_mini/defs/partition_backfill_strategies/parallel_processpool.py"
  language="python"
  title="src/project_mini/defs/partition_backfill_strategies/parallel_processpool.py"
/>

**Best for:** CPU-intensive computations, data transformations

**Parallelism:** Limited by CPU cores
