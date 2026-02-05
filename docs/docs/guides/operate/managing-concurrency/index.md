---
title: Managing concurrency
sidebar_label: Managing concurrency
description: How to limit the number of concurrent runs for jobs, assets, or for an instance of Dagster.
sidebar_position: 50
canonicalUrl: '/guides/operate/managing-concurrency'
slug: '/guides/operate/managing-concurrency'
---

This guide covers managing concurrency of Dagster assets, jobs, and Dagster instances to help prevent performance problems and downtime.

When your pipelines interact with rate-limited APIs, shared databases, or resource-constrained systems, it is a good idea to limit how many operations execute simultaneously. Dagster provides several mechanisms for managing concurrency at different levels of granularity.

| Mechanism                                                                                                           | Scope                  | Protects against                            | Use when                                                                                                                                                                                                                         |
| ------------------------------------------------------------------------------------------------------------------- | ---------------------- | ------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [Run queue limits](/guides/operate/managing-concurrency/run-queue-limits)                                           | Deployment             | Too many simultaneous runs                  | <ul><li>You need to limit total runs across your deployment</li><li>Backfills or sensors might launch many runs at once</li><li>Your infrastructure has fixed capacity for concurrent runs</li></ul>                             |
| [Concurrency pools](/guides/operate/managing-concurrency/concurrency-pools)                                         | Cross-run              | Overloading shared resources                | <ul><li>You need to protect a shared resource (database, API) across all runs</li><li>Multiple runs might simultaneously access the same external system</li><li>You want ops to queue until the resource is available</li></ul> |
| [Run executor limits](/guides/operate/managing-concurrency/run-executor-limits)                                     | Single run             | Memory/CPU exhaustion                       | <ul><li>You want to control parallelism within a single run</li><li>Memory or CPU constraints limit how many ops can run at once</li><li>You don't need cross-run coordination</li></ul>                                         |
| [Run tag limits](/guides/operate/managing-concurrency/run-tag-limits)                                               | Single run             | Resource contention by category             | <ul><li>Different ops in the same run have different resource requirements</li><li>You want some ops to run in parallel while limiting others</li><li>You need category-based throttling within a run</li></ul>                  |
| [Branch deployment concurrency limits](/guides/operate/managing-concurrency/advanced#branch-deployment-concurrency) | All branch deployments | Branch deployments using too many resources | You are managing multi-developer teams (Dagster+ only)                                                                                                                                                                           |

:::tip Combining mechanisms to manage concurrency

You can combine the mechanisms listed in the table above to manage concurrency. For example:

- **Pools + run executor limits:** Protect external resources while also limiting local parallelism
- **Run queue + pools:** Limit total runs AND protect specific resources within those runs
- **Tag limits + pools:** Fine-grained control within runs plus cross-run protection

```yaml
concurrency:
  runs:
    max_concurrent_runs: 10
  pools:
    default_limit: 3
```

:::
