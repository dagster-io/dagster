---
title: Dynamic fanout
description: How to implement dynamic fanout patterns for parallel processing.
last_update:
  author: Dennis Hume
sidebar_custom_props:
  logo: images/dagster-primary-mark.svg
---

In this example, we'll explore how to implement dynamic fanout patterns in Dagster. Dynamic fanout is useful when you need to process a variable number of items in parallel, where the exact count isn't known until runtime. This is particularly valuable for data processing pipelines that need to handle varying workloads efficiently.

## Problem: Variable workload processing

Imagine you have a data processing pipeline that receives multiple related records, where each record contains 10-30 processing units that require expensive computation. Without dynamic fanout, you'd have to do one of the following:

- Process everything sequentially (slow)
- Pre-define a fixed number of parallel processes (inflexible)
- Process all units in a single large operation (difficult to debug and monitor)

The challenge is creating a pipeline that can:

- Dynamically spawn sub-pipelines based on input data
- Process each record's units in parallel
- Collect and aggregate results efficiently
- Maintain proper lineage and observability

## Solution 1: Sequential processing within sub-pipelines

The first approach uses dynamic fanout to create parallel sub-pipelines for each record, but processes units within each sub-pipeline sequentially. This provides the first layer of parallelization.

<CodeExample
  path="docs_projects/project_mini/src/project_mini/defs/dynamic_fanout/dynamic_fanout.py"
  language="python"
  title="src/project_mini/defs/dynamic_fanout/dynamic_fanout.py"
  startAfter="# Option A"
  endBefore="# Option B"
/>

This approach creates a sub-pipeline for each input record:

1. **Dynamic trigger**: Uses <PyObject section="dynamic" module="dagster" object="DynamicOut" /> to create one sub-pipeline per input record
2. **Sequential unit processing**: Processes 10-30 units within each sub-pipeline sequentially
3. **Result aggregation**: Combines unit results into a final record output

| Processing layer | Parallelization | Units per record               |
| ---------------- | --------------- | ------------------------------ |
| Record-level     | Parallel        | 1 sub-pipeline per record      |
| Unit-level       | Sequential      | 10-30 units processed in order |

### Solution 2: Parallel processing within sub-pipelines

The second approach adds a second layer of parallelization by processing units within each sub-pipeline in parallel using multiprocessing.

<CodeExample
  path="docs_projects/project_mini/src/project_mini/defs/dynamic_fanout/dynamic_fanout.py"
  language="python"
  title="src/project_mini/defs/dynamic_fanout/dynamic_fanout.py"
  startAfter="# Option B"
  endBefore="@dg.op"
/>

This enhanced approach provides two layers of parallelization:

1. **Record-level parallelization**: Multiple sub-pipelines run simultaneously
2. **Unit-level parallelization**: Within each sub-pipeline, units are processed using a multiprocessing pool
3. **Automatic scaling**: Number of processes adapts to available CPU cores and workload size

| Processing layer | Parallelization | Performance benefit           |
| ---------------- | --------------- | ----------------------------- |
| Record-level     | Parallel        | Scales with number of records |
| Unit-level       | Parallel        | Scales with CPU cores         |

### Complete pipeline implementation

The complete pipeline uses a [graph-backed asset](/guides/build/assets/graph-backed-assets) to orchestrate the dynamic fanout pattern:

<CodeExample
  path="docs_projects/project_mini/src/project_mini/defs/dynamic_fanout/dynamic_fanout.py"
  language="python"
  title="src/project_mini/defs/dynamic_fanout/dynamic_fanout.py"
  startAfter="@dg.graph_asset"
  endBefore="@dg.asset"
/>

Key features of this implementation:

1. **Dynamic triggering**: `trigger_sub_pipelines()` creates sub-pipelines based on input data
2. **Parallel execution**: `.map()` processes each record in its own sub-pipeline
3. **Synchronization barrier**: `.collect()` ensures all sub-pipelines complete before proceeding
4. **Result aggregation**: `collect_sub_pipeline_results()` processes all results together

The graph-backed asset approach provides:

- **Full observability**: Each sub-pipeline execution is tracked individually
- **Proper lineage**: Clear dependency relationships between operations
- **Fault tolerance**: Failed sub-pipelines can be retried independently
- **Scalability**: Automatically adapts to varying input sizes
