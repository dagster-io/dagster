---
title: Avoiding pod eviction in Kubernetes deployments
description: How to handle pod eviction in Kubernetes deployments.
sidebar_position: 4400
---

When Dagster is run in Kubernetes environments, pod evictions can occur due to resource constraints or node scaling operations. To prevent runs from hanging indefinitely, you can implement the following solutions:

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
