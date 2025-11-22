---
title: Avoiding pod eviction in Kubernetes deployments
description: How to handle pod eviction in Kubernetes deployments.
sidebar_position: 4400
---

When Dagster is run in Kubernetes environments, pod evictions can occur due to resource constraints or node scaling operations. To prevent runs from hanging indefinitely, you can implement the following solutions:

- Request more resources during pod creation
- [Update pod annotation](https://kubernetes.io/docs/reference/labels-annotations-taints/#cluster-autoscaler-kubernetes-io-safe-to-evict) to prevent the cluster autoscaler from evicting important pods:

    ```
    "cluster-autoscaler.kubernetes.io/safe-to-evict": "false"
    ```
- Configure job-specific timeouts in your Dagster configuration to ensure runs don't hang indefinitely:

    ```python
    @job(
        config={
            "execution": {
                "config": {
                    "max_concurrent": 1,
                    "timeout_seconds": 7200  # 2 hours
                }
            }
        }
    )
    ```
- Configure Dagster [run monitoring](/deployment/execution/run-monitoring) to detect and restart crashed run workers






