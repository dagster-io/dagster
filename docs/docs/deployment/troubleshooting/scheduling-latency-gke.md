---
title: Measuring scheduling latency in Dagster on GKE
sidebar_position: 1400
description: How to measure and analyze the time between when a Kubernetes pod could start and when it actually starts executing a Dagster step.
---

## Problem description

Users may need to measure scheduling latency in Dagster deployments on GKE, specifically tracking the time between when a Kubernetes worker pod is ready and when the step execution actually begins. This is useful for identifying resource bottlenecks or autoscaler delays.

## Solution

Use Dagster's built-in event logging system to track execution phases and calculate scheduling latency.

### Relevant event types

Dagster emits the following step-level events that you can use to measure latency:

| Event                  | Meaning                                      |
| ---------------------- | -------------------------------------------- |
| `STEP_WORKER_STARTING` | The subprocess or pod is being launched.     |
| `STEP_WORKER_STARTED`  | The worker process has started and is ready. |
| `STEP_START`           | The actual op execution begins.              |

Calculate scheduling latency by measuring the time difference between `STEP_WORKER_STARTED` and `STEP_START`. This captures how long a job waited after the worker was ready before execution began.

### Accessing event logs via GraphQL

You can access Dagster event logs programmatically using the GraphQL API:

1. Use the `runsOrError` query to retrieve job runs.
2. Use the `CapturedLogs` query to retrieve log data for a specific run.

For more details on the GraphQL API, see the [GraphQL API reference](/api/graphql).

### Alternative: custom log storage

If you need logs stored in a location other than the default Dagster+ S3 bucket, configure a custom `ComputeLogManager`. For Google Cloud Storage, see the [GCS ComputeLogManager documentation](/integrations/libraries/obstore#gcscomputelogmanager).

## Prevention

Set up automated monitoring of these event logs to proactively identify scheduling bottlenecks and resource constraints in your Kubernetes cluster.

## Related documentation

- [Dagster logging](/guides/log-debug/logging)
- [GraphQL API](/api/graphql)
- [Deploying Dagster to Kubernetes with Helm](/deployment/oss/deployment-options/kubernetes/deploying-to-kubernetes)
