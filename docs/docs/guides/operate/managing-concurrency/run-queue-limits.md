---
title: Run queue limits
description: Configuring a run queue limit to limit the total number of concurrent runs across an entire deployment.
sidebar_position: 100
---

To limit the total number of runs that can be in progress at the same time across your entire deployment, you can set a run queue limit.

- In Dagster OSS, add the following to your [dagster.yaml](/deployment/oss/dagster-yaml)
- In Dagster+, add the following to your [full deployment settings](/deployment/dagster-plus/deploying-code/full-deployments/full-deployment-settings-reference)

```yaml
concurrency:
  runs:
    max_concurrent_runs: 15
```
