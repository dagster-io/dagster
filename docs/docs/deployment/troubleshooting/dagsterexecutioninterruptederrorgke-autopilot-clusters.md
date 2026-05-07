---
title: DagsterExecutionInterruptedError randomly raised in GKE Autopilot clusters
sidebar_position: 80
description: How to resolve DagsterExecutionInterruptedError caused by pod preemption during node initialization on GKE Autopilot.
---

## Problem description

When running Dagster on GKE Autopilot clusters, you may encounter `DagsterExecutionInterruptedError` due to pod preemption during node initialization.

- The error can occur randomly but is more frequent with jobs that have higher execution frequency.
- The issue happens when new compute nodes are added to handle resource demands, but pods are scheduled before node initialization is complete.
- To resolve this, configure job-level retries in your Dagster deployment settings to allow for automatic re-execution on initialized nodes.

## Solution

To implement the solution:

1. In your Dagster+ deployment settings, set `max_retries` to 1 (or higher if needed).
2. This allows jobs to retry automatically if they fail due to preemption.
3. The retry will typically execute on an initialized node and complete successfully.

:::note

This issue is distinct from pod eviction and timeout problems. While setting `DAGSTER_DBT_CLOUD_POLL_TIMEOUT` or adding pod annotations like `"cluster-autoscaler.kubernetes.io/safe-to-evict": "false"` may help with other issues, they won't resolve preemption-related interruptions.

:::

## Related documentation

- [Deploying Dagster to Kubernetes with Helm](/deployment/oss/deployment-options/kubernetes/deploying-to-kubernetes)
- [Dagster+ deployment documentation](/deployment/dagster-plus)
