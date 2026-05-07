---
title: Code location deployment fails due to container configuration
sidebar_position: 50
description: Add the required containerConfig key to your Dagster+ agent configuration to avoid code location deployment failures.
---

## Problem description

Users may encounter deployment failures when attempting to deploy code locations with container configurations in Dagster+. This issue can occur even when the same configuration works in other environments, typically manifesting as an error related to container limits.

## Symptoms

- Code location deployment fails in one environment but works in another.
- Error messages related to container configuration or resource limits.
- Deployment failures persist even after adjusting resource limits in the code location configuration.

## Root cause

The issue occurs when the Dagster+ agent configuration is missing the required `containerConfig` key in the YAML configuration, even if there are no specific values set for it. This prevents proper handling of container configurations specified in code locations.

## Solution

Add the `containerConfig` key to your Dagster+ agent configuration YAML, even if empty:

```yaml
serverK8sConfig:
  containerConfig: # raw config for the pod's main container
  podSpecConfig: # raw config for the spec of the launched pod
    nodeSelector:
```

### Step-by-step resolution

1. Locate your Dagster+ agent configuration file.
2. Add the `containerConfig` key under `serverK8sConfig` as shown in the example above.
3. Redeploy your Dagster+ agent with the updated configuration.
4. Attempt to deploy your code location again with the desired container configuration.

### Alternative solutions

If issues persist, verify:

- Kubernetes resource quotas in your environment
- Node resources availability
- Matching Dagster versions across environments

## Prevention

Always include the `containerConfig` key in your Dagster+ agent configuration when working with containerized deployments, even if you don't need to specify any values for it initially.
