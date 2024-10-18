---
title: 'Serverless run isolation'
displayed_sidebar: 'dagsterPlus'
sidebar_label: 'Run isolation'
sidebar_position: 40
---

# Serverless run isolation

Dagster+ Serverless offers two settings for run isolation: isolated and non-isolated. Isolated runs are the default and are intended for production, while non-isolated runs are intended for faster iteration during development.

<details>
  <summary>Prerequisites</summary>

To follow the steps in this guide, you'll need:

- An active Dagster+ Serverless deployment
- An understanding of [Dagster+ deployment settings](/dagster-plus/deployment/settings)
</details>

---

## Differences between isolated and non-isolated runs

- [**Isolated runs**](#isolated-runs-default) execute in their own container. They're the default and are intended for production and compute-heavy use cases.
- [**Non-isolated runs**](#non-isolated-runs) trade off isolation for speed. They must be launched manually and are intended for fast iteration during development.

## Isolated runs (default)

Isolated runs each take place in their own container with their own compute resources: 4 vCPUs and 16GB of RAM.

These runs may take up to 3 minutes to start while these resources are provisioned.

When launching runs manually, select `Isolate run environment` in the Launchpad to launch an isolated runs.

:::note

If non-isolated runs are disabled (see the section below), the toggle won't appear and all runs will be isolated.
:::

## Non-isolated runs

This can be enabled or disabled in deployment settings with

```yaml
non_isolated_runs:
  enabled: True
```

Non-isolated runs provide a faster start time by using a standing, shared container for each code location.

They have fewer compute resources: 0.25 vCPUs and 1GB of RAM. These resources are shared with other processes running within a code location like sensors. As a result, it's recommended to use isolated runs for compute intensive jobs and asset materializations.

While launching runs from the Launchpad, un-check `Isolate run environment`. When materializing an asset, shift-click `Materialize all` to open the Launchpad and un-check the `Isolate run environment` checkbox.

:::warning

To avoid crashes and memory exhaustion, only one non-isolated run will execute at once by default. While a non-isolated run is in progress, the Launchpad will only allow isolated runs to be launched.

This limit can be configured in [deployment settings](/dagster-plus/deployment/settings).

```yaml
non_isolated_runs:
  enabled: True
  max_concurrent_non_isolated_runs: 1
```

:::
