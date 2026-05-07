---
title: Pod evictions occurring in Kubernetes deployments
sidebar_position: 160
description: How to handle pod eviction in Kubernetes deployments.
---

## Problem description

When Dagster is run in Kubernetes environments, pod evictions can occur due to resource constraints or node scaling operations.

## Solution

To prevent runs from hanging indefinitely, you can implement the following solutions:

- Request more resources during pod creation to reduce the likelihood of eviction due to resource pressure:

  ```python
  from dagster_k8s import k8s_job_executor

  @job(
      executor_def=k8s_job_executor.configured({
          "container_config": {
              "resources": {
                  "requests": {"cpu": "1000m", "memory": "64Mi"},
                  "limits": {"cpu": "2000m", "memory": "2560Mi"}
              }
          }
      })
  )
  ```

- [Update pod annotation](https://kubernetes.io/docs/reference/labels-annotations-taints/#cluster-autoscaler-kubernetes-io-safe-to-evict) to prevent the cluster autoscaler from evicting important pods by adding the following annotation:

  ```python
  from dagster_k8s import k8s_job_executor

  @job(
      executor_def=k8s_job_executor.configured({
          "pod_template_spec_metadata": {
              "annotations": {
                  "cluster-autoscaler.kubernetes.io/safe-to-evict": "false"
              }
          }
      })
  )
  ```

- Configure job-specific timeouts in your Dagster configuration to ensure runs don't hang indefinitely:

  ```python
  from dagster_k8s import k8s_job_executor

  @job(
      executor_def=k8s_job_executor.configured({
          "job_wait_timeout": 7200  # 2 hours
      })
  )
  ```

- Configure Dagster [run monitoring](/deployment/execution/run-monitoring) to detect and restart crashed run workers

### Issues with pod preemption in GKE Autopilot

Pod preemption can also cause job failures in Kubernetes environments like GKE Autopilot. You can prevent this by configuring `tolerations` and `nodeSelector` settings in your Helm chart configuration.

#### Configuration placement

These configurations should be placed under `podSpecConfig` (not `jobSpecConfig`) in your Helm chart, as `tolerations` and `nodeSelector` are fields on the pod spec (`spec.template.spec`) rather than the job spec (`job.spec`).

#### Example configuration

Add the following to your Helm chart values:

```yaml
workspace:
  runK8sConfig:
    podSpecConfig:
      tolerations:
        - key: 'example-key'
          operator: 'Equal'
          value: 'example-value'
          effect: 'NoSchedule'
      nodeSelector:
        workload-type: 'batch'
```

#### Benefits

This approach provides several advantages:

- **Cross-platform compatibility:** Works across different cluster autoscalers and cloud providers, not just specific solutions like Karpenter.
- **Granular control:** Offers fine-grained control over pod scheduling and eviction behavior.
- **GKE Autopilot support:** Particularly effective in GKE Autopilot environments where pod preemption is common.
- **Standard Kubernetes:** Uses standard Kubernetes tolerations and nodeSelector configurations.

#### Use cases

This configuration is especially useful when:

- Running long-running Dagster jobs that shouldn't be interrupted
- Working in environments with aggressive cluster autoscaling
- Needing to ensure job completion without preemption-related failures
- Managing workloads in shared Kubernetes clusters
