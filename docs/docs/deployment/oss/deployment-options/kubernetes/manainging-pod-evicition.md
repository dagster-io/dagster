---
title: 'Handling pod eviction'
description: How to handle pod eviction in Kubernetes deployments.
sidebar_position: 4400
---

When running Dagster in Kubernetes environments, pod evictions can occur due to resource constraints or node scaling operations. To prevent runs from hanging indefinitely, you can implement the following solutions:

```
"cluster-autoscaler.kubernetes.io/safe-to-evict": "false"
```

Configure job-specific timeouts in your Dagster configuration to ensure runs don't hang indefinitely:

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

Pod evictions can occur due to:

- Node running out of memory
- Node scale-down operations
- Resource limit constraints to mitigate these issues, consider requesting more resources during pod creation and implementing appropriate timeout configurations.

## Next steps

- Learn more about [run monitoring and timeout configurations](/deployment/execution/run-monitoring)
