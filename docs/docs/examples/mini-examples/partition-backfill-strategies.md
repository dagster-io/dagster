---
title: Partition backfill strategies
description: Comparing backfill strategies for partitioned assets - one run per partition, batched runs, or single run.
last_update:
  author: Dennis Hume
sidebar_custom_props:
  logo: images/dagster-primary-mark.svg
---

In this example, we'll explore three different strategies for [backfilling](/guides/build/partitions-and-backfills/backfilling-data) partitioned assets. When you need to materialize multiple partitions (for initial setup or reprocessing), you can choose between Dagster's default one-run-per-partition approach, a batched approach, or a single-run approach using <PyObject section="partitions" module="dagster" object="BackfillPolicy" />. Each strategy has distinct trade-offs in terms of overhead, fault isolation, and resource utilization.

## Problem: Backfilling 100 days of historical data

Imagine you need to backfill 100 days of historical event data. Each day's data needs to be processed and stored. Without optimization, this could mean launching 100 separate runs, each with its own overhead. But processing everything in one run means a single failure requires reprocessing all 100 days.

The key question is: How should you batch your partitions to balance overhead, fault isolation, and performance?

### Solution 1: One run per partition (default)

By default, Dagster launches one run per partition. This provides maximum observability and fault isolation—if one partition fails, others continue independently, and partitions are individually retried. This solution is best for dealing with unreliable data sources or API rate limits. However, each run adds overhead (startup time, resource allocation).

<CodeExample
  path="docs_projects/project_mini/src/project_mini/defs/partition_backfill_strategies/multi_run_backfill.py"
  language="python"
  title="src/project_mini/defs/partition_backfill_strategies/multi_run_backfill.py"
/>

|                       | **One run per partition**                       |
| --------------------- | ----------------------------------------------- |
| **Runs created**      | 100 runs for 100 partitions                     |
| **Fault isolation**   | Maximum - failed partitions don't affect others |
| **Retry granularity** | Retry individual partitions                     |
| **Overhead**          | Highest (run startup cost × 100)                |
| **Best for**          | Unreliable data sources, API rate limits        |

### Solution 2: Batched runs

With <PyObject section="partitions" module="dagster" object="BackfillPolicy.multi_run"/>, Dagster groups partitions into batches. For example, with `max_partitions_per_run=10`, 100 partitions become 10 runs of 10 partitions each. This balances overhead reduction with fault isolation.

<CodeExample
  path="docs_projects/project_mini/src/project_mini/defs/partition_backfill_strategies/batched_backfill.py"
  language="python"
  title="src/project_mini/defs/partition_backfill_strategies/batched_backfill.py"
/>

|                       | **Batched runs (10 per run)**           |
| --------------------- | --------------------------------------- |
| **Runs created**      | 10 runs for 100 partitions              |
| **Fault isolation**   | Moderate - failure affects batch of 10  |
| **Retry granularity** | Retry batches of 10 partitions          |
| **Overhead**          | Moderate (run startup cost × 10)        |
| **Best for**          | Balancing overhead with fault tolerance |

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

Adjust based on observed failure rates and infrastructure constraints.

### Solution 3: Single run

With <PyObject section="partitions" module="dagster" object="BackfillPolicy.single_run"/>, Dagster processes all selected partitions in one run. This eliminates per-run overhead and is ideal when your processing engine (Spark, Snowflake, etc.) handles parallelism internally.

<CodeExample
  path="docs_projects/project_mini/src/project_mini/defs/partition_backfill_strategies/single_run_backfill.py"
  language="python"
  title="src/project_mini/defs/partition_backfill_strategies/single_run_backfill.py"
/>

|                       | **Single run**                       |
| --------------------- | ------------------------------------ |
| **Runs created**      | 1 run for all 100 partitions         |
| **Fault isolation**   | None - failure affects all           |
| **Retry granularity** | Must retry all partitions together   |
| **Overhead**          | Lowest (single run startup cost)     |
| **Best for**          | Spark/Snowflake, range-based queries |

## When to use each approach

| Factor              | One per partition | Batched               | Single run     |
| ------------------- | ----------------- | --------------------- | -------------- |
| **Run overhead**    | High (N runs)     | Medium (N/batch runs) | Low (1 run)    |
| **Fault isolation** | Best              | Moderate              | None           |
| **Retry cost**      | 1 partition       | 1 batch               | All partitions |
| **Observability**   | Per partition     | Per batch             | Aggregate only |

**Use one run per partition when:**

- Your data source is unreliable (API rate limits, transient failures)
- You need fine-grained retry capability for individual partitions
- Per-partition observability is critical

**Use batched runs when:**

- You want to reduce overhead while maintaining some fault isolation
- Processing time per partition is short (seconds to a few minutes)
- You're doing an initial backfill of many partitions

**Use single run when:**

- You're using a parallel-processing engine (Spark, Snowflake, Databricks)
- Your queries naturally operate on date ranges
- You want to minimize Dagster Cloud credit consumption

| Scenario                                   | Recommended strategy        |
| ------------------------------------------ | --------------------------- |
| API with rate limits or transient failures | One per partition           |
| Short processing time, reliable source     | Batched (10-50 per run)     |
| Spark/Snowflake with range queries         | Single run                  |
| Cost optimization in Dagster Cloud         | Single run or large batches |
| Initial backfill of 1000+ partitions       | Batched (50-100 per run)    |

## Parallelization within batched runs

When using <PyObject section="partitions" module="dagster" object="BackfillPolicy.multi_run"/>, you get multiple partitions in a single run. Here are different ways to parallelize processing within that run.

### Strategy 1: Batch query (fastest for databases)

Process all partitions in a single database query:

<CodeExample
  path="docs_projects/project_mini/src/project_mini/defs/partition_backfill_strategies/parallel_batch_query.py"
  language="python"
  title="src/project_mini/defs/partition_backfill_strategies/parallel_batch_query.py"
/>

**Best for:** SQL databases, REST APIs with batch endpoints

### Strategy 2: Thread pool (I/O-bound operations)

Use threads for parallel I/O operations:

<CodeExample
  path="docs_projects/project_mini/src/project_mini/defs/partition_backfill_strategies/parallel_threadpool.py"
  language="python"
  title="src/project_mini/defs/partition_backfill_strategies/parallel_threadpool.py"
/>

**Best for:** HTTP requests, file I/O, database queries

**Parallelism:** Limited by `max_workers` (5 concurrent in this example)

### Strategy 3: Process pool (CPU-bound operations)

Use processes for parallel CPU-intensive work:

<CodeExample
  path="docs_projects/project_mini/src/project_mini/defs/partition_backfill_strategies/parallel_processpool.py"
  language="python"
  title="src/project_mini/defs/partition_backfill_strategies/parallel_processpool.py"
/>

**Best for:** CPU-intensive computations, data transformations

**Parallelism:** Limited by CPU cores

### Comparison of parallelization strategies

| Strategy     | Best for        | Max concurrency     | Overhead | Complexity |
| ------------ | --------------- | ------------------- | -------- | ---------- |
| Batch query  | SQL databases   | N/A (single query)  | Very low | Very low   |
| Thread pool  | I/O-bound tasks | 10-100 threads      | Low      | Low        |
| Process pool | CPU-bound tasks | Number of CPU cores | Medium   | Low        |
