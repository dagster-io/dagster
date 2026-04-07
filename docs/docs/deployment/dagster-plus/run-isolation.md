---
description: Dagster+ run isolation offers isolated runs for production with dedicated resources, and non-isolated runs in a standing, shared container for faster development.
sidebar_label: Run isolation
sidebar_position: 450
title: Run isolation
tags: [dagster-plus-feature]
---

Dagster+ offers two settings for run isolation: isolated and non-isolated. These settings are available for both [Serverless](/deployment/dagster-plus/serverless) and [Hybrid](/deployment/dagster-plus/hybrid) deployments.

- [**Isolated runs**](#isolated-runs-default) execute in their own container. They're the default and are intended for production and compute-heavy use cases.
- [**Non-isolated runs**](#non-isolated-runs) trade off isolation for speed. They are intended for fast iteration during development or for time-sensitive jobs that do not require extensive compute within Dagster.

## Isolated runs (default)

Isolated runs each take place in their own container with their own compute resources.

- **Serverless**: 4 vCPUs and 16GB of RAM
- **Hybrid**: Resources are determined by your infrastructure configuration

These runs may take up to 3 minutes to start while resources are provisioned.

When launching runs manually, select `Isolate run environment` in the Launchpad to launch an isolated run.

:::note

If non-isolated runs are disabled (see the section below), the toggle won't appear and all runs will be isolated.
:::

## Non-isolated runs

Non-isolated runs provide a faster start time by using a standing, shared container for each code location.

They have fewer compute resources than isolated runs. For Serverless deployments, non-isolated runs receive 0.25 vCPUs and 1GB of RAM. These resources are shared with other processes running within a code location like sensors. As a result, it's recommended to use isolated runs for compute intensive jobs and asset materializations.

To be able to use non-isolated runs, the `non_isolated_runs` setting must first be enabled in [Full deployment settings](/deployment/dagster-plus/deploying-code/full-deployments/full-deployment-settings-reference#non-isolated-runs):

```yaml
non_isolated_runs:
  enabled: True
```

When materializing assets in the Dagster+ UI, you can shift-click the `Materialize` button to open the Launchpad and then un-check the `Isolate run environment` checkbox.

You can also programmatically indicate that a run should be a non-isolated run by applying the run tag `dagster/isolation: disabled`:

```python
define_asset_job(tags={"dagster/isolation": "disabled"}, ...)
```

:::warning

To avoid crashes and memory exhaustion, only one non-isolated run will execute at once by default. While a non-isolated run is in progress, the Launchpad will only allow isolated runs to be launched.

This limit can be configured in [deployment settings](/deployment/dagster-plus/deploying-code/full-deployments/full-deployment-settings-reference#non-isolated-runs).

```yaml
non_isolated_runs:
  enabled: True
  max_concurrent_non_isolated_runs: 1
```

:::
