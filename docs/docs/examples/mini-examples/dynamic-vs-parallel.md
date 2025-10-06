---
title: Dynamic outputs vs Python parallelism
description: Comparing Dagster's dynamic outputs with regular Python parallelism for concurrent processing.
last_update:
  author: Dennis Hume
sidebar_custom_props:
  logo: images/dagster-primary-mark.svg
---

In this example, we'll explore two different approaches to achieving parallelism in Dagster pipelines. When you have computationally expensive operations that can benefit from parallel processing, you can choose between Dagster's built-in dynamic outputs or standard Python parallelism techniques. Each approach has distinct trade-offs in terms of observability, performance, and resource consumption.

## Problem: Parallel processing of multiple items

Imagine you need to process a collection of items (in our example, letters a-z), where each item requires some computation time (simulated with a sleep operation). Without parallelism, processing each item sequentially would take much longer than processing them concurrently.

The key question is: Should you use Dagster's dynamic outputs to create separate op executions for each item, or should you handle the parallelism within a single op using Python's multiprocessing capabilities?

### Solution 1: Dagster dynamic outputs

[Dynamic outputs](/api/dagster/dynamic#dagster.DynamicOutput) allow you to create separate op executions for each item. In this example, each letter (a-z) gets its own op execution. This approach provides maximum observability and leverages Dagster's built-in retry mechanisms, but comes with additional overhead for each item.

<CodeExample
  path="docs_projects/project_mini/src/project_mini/defs/dynamic_vs_parallel/dynamic_outputs.py"
  language="python"
  title="src/project_mini/defs/dynamic_vs_parallel/dynamic_outputs.py"
/>

|                    | **Dynamic outputs approach**                         |
| ------------------ | ---------------------------------------------------- |
| **Execution time** | ~26 seconds (1 second per letter + Dagster overhead) |
| **Observability**  | Full visibility into each letter's execution         |
| **Retry logic**    | Automatic retry for individual letters               |
| **Resource usage** | Each letter consumes a credit in Dagster Cloud       |
| **Complexity**     | Simple dynamic pattern setup                         |

### Solution 2: Python parallelism

The Python parallelism approach uses multiprocessing within a single op to process all letters concurrently. This provides better performance than Dagster's dynamic outputs approach by utilizing multiple CPU cores simultaneously, but requires manual implementation of error handling and retry logic.

<CodeExample
  path="docs_projects/project_mini/src/project_mini/defs/dynamic_vs_parallel/python_parallelism.py"
  language="python"
  title="src/project_mini/defs/dynamic_vs_parallel/python_parallelism.py"
/>

|                    | **Python parallelism approach**                        |
| ------------------ | ------------------------------------------------------ |
| **Execution time** | ~4 seconds (parallel processing across CPU cores)      |
| **Observability**  | Limited visibility into individual letter progress     |
| **Retry logic**    | Manual implementation required                         |
| **Resource usage** | Single credit consumption for entire operation         |
| **Complexity**     | Simple multiprocessing setup, familiar Python patterns |

## When to use each approach

The choice between dynamic outputs and Python parallelism depends on your specific requirements:

**Use Dagster dynamic outputs when:**

- Each item takes 5+ minutes to process (overhead is negligible)
- Individual item observability is critical
- You need fine-grained retry capabilities
- You want to leverage Dagster's built-in monitoring and alerting
- The cost of additional credits in Dagster+ is acceptable

**Use Python parallelism when:**

- Each item takes seconds to minutes to process
- Overall job performance is more important than granular visibility
- You want to minimize resource consumption (credits/compute)
- You're comfortable implementing custom error handling
- You have CPU-bound work that benefits from true parallelism

## Hybrid approach

You can also combine both approaches: use Python parallelism within individual ops of a dynamically generated graph. This allows you to balance the granularity of Dagster's observability with the performance benefits of Python parallelism.

For example, you might dynamically create ops for major processing stages, then use multiprocessing within each stage to process multiple items concurrently.
