---
title: Resource caching
description: How to handling caching within resources.
last_update:
  author: Dennis Hume
sidebar_custom_props:
  logo: images/dagster-primary-mark.svg
---

In this example, we'll explore different ways to handle caching in Dagster. Caching is especially useful for assets that rely on expensive operations, such as API calls, database queries, or heavy computations, as it can dramatically improve performance, reduce costs, and make pipelines more efficient. In practice, it’s usually best to implement caching within [resources](/guides/build/external-resources) rather than [assets](/guides/build/assets), since this makes the functionality easier to share and reuse.

### Problem: Expensive resource

Imagine a simple resource `ExpensiveResource` with an `addition` method that includes a forced 5-second sleep. Without caching, the resource executes the method from scratch every time it’s called. Because no intermediate results are stored, repeated calls with the same inputs always re-run the computation and incur the full cost.

<CodeExample
  path="docs_projects/project_mini/src/project_mini/defs/resource_caching/expensive_resource.py"
  language="python"
  title="src/project_mini/defs/resource_caching/expensive_resource.py"
/>

|                | `expensive_asset` | `another_expensive_asset` |
| -------------- | ----------------- | ------------------------- |
| Execution Time | 15 seconds        | 15 seconds                |

### Solution 1: Caching within the resource

The in-memory caching implementation uses Python’s `@[functools.lru_cache](https://docs.python.org/3/library/functools.html#functools.cache)` decorator to store results of the `addition` method. Once a particular set of arguments has been computed, the result is stored in memory within the resource. Subsequent calls with the same arguments return immediately from the cache instead of redoing the expensive operation.

However, because each asset initializes its own resource, cached results are not shared across asset executions.

<CodeExample
  path="docs_projects/project_mini/src/project_mini/defs/resource_caching/expensive_resource_cache.py"
  language="python"
  title="src/project_mini/defs/assets.py"
/>

|                | `expensive_asset_cache` | `another_expensive_asset_cache` |
| -------------- | ----------------------- | ------------------------------- |
| Execution Time | 5 seconds               | 5 seconds                       |

### Solution 2: External caching

The external caching implementation persists results to disk using a [pickle](https://docs.python.org/3/library/pickle.html) file. At runtime, the resource loads the cache from the file, checks whether a result already exists for the given arguments, and saves new results after computation. This approach ensures that the cache survives process restarts and can be reused across assets, even if each initializes its own resource.

<CodeExample
  path="docs_projects/project_mini/src/project_mini/defs/resource_caching/expensive_resource_pickle.py"
  language="python"
  title="src/project_mini/defs/assets.py"
/>

|                | `expensive_asset_pickle` | `another_expensive_asset_pickle` |
| -------------- | ------------------------ | -------------------------------- |
| Execution Time | 5 seconds (on first run) | < 1 second                       |

:::note

Using a pickle file assumes that all assets execute on the same node. Depending on how you execute Dagster you might want to use an external caching layer such as [AWS Dynamo](https://aws.amazon.com/dynamodb/) or [Redis](https://redis.io/) that your assets have access to.

:::
