---
title: Concurrency controls
description: Comparing different approaches to limit concurrent execution in Dagster.
last_update:
  author: Dennis Hume
sidebar_custom_props:
  logo: images/dagster-primary-mark.svg
---

In this example, we'll explore different approaches to control concurrency in Dagster. When your pipelines interact with rate-limited APIs, shared databases, or resource-constrained systems, you need to limit how many operations execute simultaneously. Dagster provides several mechanisms at different levels of granularity.

## Problem: Preventing resource overload

Imagine you have assets that query a database with limited connection pools, call rate-limited APIs, or consume significant memory. Running too many of these operations simultaneously can cause failures, throttling, or performance degradation.

The key question is: At what level should you limit concurrency—across all runs, within a single run, or for specific resources?

### Solution 1: Concurrency pools (cross-run limits)

Concurrency pools limit how many assets or ops with the same pool can execute simultaneously across all runs. This is ideal for protecting shared resources like databases or APIs.

<CodeExample
  path="docs_projects/project_mini/src/project_mini/defs/concurrency_controls/pool_concurrency.py"
  language="python"
  title="src/project_mini/defs/concurrency_controls/pool_concurrency.py"
/>

Configure pool limits in your deployment settings ([dagster.yaml](/deployment/oss/dagster-yaml) or [Dagster+](/deployment/dagster-plus) settings):

```yaml
concurrency:
  pools:
    default_limit: 5
```

Or set specific pool limits via CLI: `dagster instance concurrency set database 2`

|                   | **Concurrency pools**                           |
| ----------------- | ----------------------------------------------- |
| **Scope**         | Across all runs in the deployment               |
| **Granularity**   | Per asset/op with same pool name                |
| **Configuration** | Pool name on asset + limit in deployment config |
| **Best for**      | Database connections, API rate limits           |

### Solution 2: Executor concurrency (within-run limits)

Executor concurrency limits how many ops execute simultaneously within a single run. This controls parallelism without affecting other runs.

<CodeExample
  path="docs_projects/project_mini/src/project_mini/defs/concurrency_controls/executor_concurrency.py"
  language="python"
  title="src/project_mini/defs/concurrency_controls/executor_concurrency.py"
/>

|                   | **Executor concurrency**       |
| ----------------- | ------------------------------ |
| **Scope**         | Within a single run            |
| **Granularity**   | All ops in the run             |
| **Configuration** | `max_concurrent` on executor   |
| **Best for**      | Memory constraints, CPU limits |

### Solution 3: Tag-based concurrency (grouped limits)

Tag-based concurrency limits ops with specific tags, allowing fine-grained control within a run. Multiple ops can run in parallel, but only N with a given tag.

<CodeExample
  path="docs_projects/project_mini/src/project_mini/defs/concurrency_controls/tag_concurrency.py"
  language="python"
  title="src/project_mini/defs/concurrency_controls/tag_concurrency.py"
/>

|                   | **Tag-based concurrency**                     |
| ----------------- | --------------------------------------------- |
| **Scope**         | Within a single run                           |
| **Granularity**   | Ops with matching tag key/value               |
| **Configuration** | `tag_concurrency_limits` on executor          |
| **Best for**      | Mixed workloads with different resource needs |

### Solution 4: Run queue limits (deployment-wide)

Run queue limits control how many runs can be in progress simultaneously across your entire deployment. Configure in deployment settings:

```yaml
concurrency:
  runs:
    max_concurrent_runs: 10
    tag_concurrency_limits:
      - key: 'dagster/backfill'
        limit: 3
```

|                   | **Run queue limits**                         |
| ----------------- | -------------------------------------------- |
| **Scope**         | Entire deployment                            |
| **Granularity**   | Whole runs                                   |
| **Configuration** | Deployment settings (`dagster.yaml`)         |
| **Best for**      | Overall system capacity, backfill management |

## When to use each approach

| Control type      | Scope      | Protects against                | Example use case           |
| ----------------- | ---------- | ------------------------------- | -------------------------- |
| Concurrency pools | Cross-run  | Overloading shared resources    | Database connection limits |
| Executor limits   | Single run | Memory/CPU exhaustion           | Large data transformations |
| Tag concurrency   | Single run | Resource contention by category | Mixed DB + API workloads   |
| Run queue limits  | Deployment | Too many simultaneous runs      | Backfill throttling        |

**Use concurrency pools when:**

- You need to protect a shared resource (database, API) across all runs
- Multiple runs might simultaneously access the same external system
- You want ops to queue until the resource is available

**Use executor limits when:**

- You want to control parallelism within a single run
- Memory or CPU constraints limit how many ops can run at once
- You don't need cross-run coordination

**Use tag-based limits when:**

- Different ops in the same run have different resource requirements
- You want some ops to run in parallel while limiting others
- You need category-based throttling within a run

**Use run queue limits when:**

- You need to limit total runs across your deployment
- Backfills or sensors might launch many runs at once
- Your infrastructure has fixed capacity for concurrent runs

## Combining approaches

These mechanisms can be combined. For example:

- **Pools + executor limits**: Protect external resources while also limiting local parallelism
- **Run queue + pools**: Limit total runs AND protect specific resources within those runs
- **Tag limits + pools**: Fine-grained control within runs plus cross-run protection

```yaml
concurrency:
  runs:
    max_concurrent_runs: 10
  pools:
    default_limit: 3
```

This configuration allows up to 10 concurrent runs, with at most 3 ops per pool executing across all runs.
