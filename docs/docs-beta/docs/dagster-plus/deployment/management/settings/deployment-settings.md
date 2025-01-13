---
title: "Deployment settings"
sidebar_position: 200
unlisted: true
---

# Dagster+ deployment settings reference

:::note
This article is applicable to Dagster+.
:::

{/* /dagster-plus */}
This reference describes the settings that can be configured for full deployments in [Dagster+](/todo.md).

{/* /dagster-plus/managing-deployments/managing-deployments#configuring-deployment-settings */}
Refer to the [Managing deployments in Dagster+ guide](/todo.md) for info about configuring settings in the Dagster+ interface or using the `dagster-cloud` CLI.

## Settings schema

Settings are formatted using YAML. For example:

```yaml
run_queue:
  max_concurrent_runs: 10
  tag_concurrency_limits:
    - key: "database"
      value: "redshift"
      limit: 5

run_monitoring:
  start_timeout_seconds: 1200
  cancel_timeout_seconds: 1200
  max_runtime_seconds: 7200

run_retries:
  max_retries: 0

sso_default_role: EDITOR
```

## Settings

For each deployment, you can configure settings for:

- [Run queue](#run-queue-run_queue)
- [Run monitoring](#run-monitoring-run_monitoring)
- [Run retries](#run-retries-run_retries)
- [SSO default role](#sso-default-role)
- [Non-isolated runs](#non-isolated-runs)

### Run queue (run_queue)

The `run_queue` settings allow you to specify how many runs can execute concurrently in the deployment.

```yaml
run_queue:
  max_concurrent_runs: 10
  tag_concurrency_limits:
    - key: "database"
      value: "redshift"
      limit: 5
```

| Property | Description |
| --- | --- |
| run_queue.max_concurrent_runs | The maximum number of runs that are allowed to be in progress at once. Set to 0 to stop any runs from launching. Negative values aren't permitted. <ul><li>**Default** - `10` (20 minutes)</li><li>**Maximum** - `500` ([Hybrid](/dagster-plus/deployment/deployment-types/hybrid/)), `50` ([Serverless](/dagster-plus/deployment/deployment-types/serverless/))</li></ul> |
| run_queue.tag_concurrency_limits | A list of limits applied to runs with particular tags. <ul><li>**Defaults** - `[]`</li></ul> Each list item may have the following properties: <ul><li>`key`</li><li>`value`</li><ul><li>If defined, the `limit` is applied only to the `key-value` pair.</li><li>If set to a dict with applyLimitPerUniqueValue: true, the `limit` is applied to the number of unique values for the `key`.</li><li>If set to a dict with `applyLimitPerUniqueValue: true`, the limit is applied to the number of unique values for the `key`.</li></ul><li>`limit`</li></ul> |

### Run monitoring (run_monitoring)

The `run_monitoring` settings allow you to define how long Dagster+ should wait for runs to start before making them as failed, or to terminate before marking them as canceled.

```yaml
run_monitoring:
  start_timeout_seconds: 1200
  cancel_timeout_seconds: 1200
  max_runtime_seconds: 7200
```

| Property | Description |
| --- | --- |
| run_monitoring.start_timeout_seconds | The number of seconds that Dagster+ will wait after a run is launched for the process or container to start executing. After the timeout, the run will fail. This prevents runs from hanging in `STARTING` indefinitely when the process or container doesn't start. <ul><li>**Default** - `1200` (20 minutes)</li></ul> |
| run_monitoring.cancel_timeout_seconds | The number of seconds that Dagster+ will wait after a run termination is initiated for the process or container to terminate. After the timeout, the run will move into a `CANCELED` state. This prevents runs from hanging in `CANCELING` indefinitely when the process or container doesn't terminate cleanly. <ul><li>**Default** - `1200` (20 minutes)</li></ul> |
| run_monitoring.max_runtime_seconds | The number of seconds that Dagster+ will wait after a run is moved into a `STARTED` state for the run to complete. After the timeout, the run will be terminated and moved into a `FAILURE` state. This prevents runs from hanging in `STARTED` indefinitely if the process is hanging. <ul><li>**Default** - `No limit`</li></ul> |

### Run retries (run_retries)

The `run_retries` settings allow you to define how Dagster+ handles retrying failed runs in the deployment.

```yaml
run_retries:
  max_retries: 0
```

| Property | Descripton |
| --- | --- |
| run_retries.max_retries | The maximum number of times Dagster+ should attempt to retry a failed run. Dagster+ will use the default if this setting is undefined. <ul><li>**Default** - `0`</li></ul> |
| run_retries.retry_on_asset_or_op_failure | Whether to retry runs that failed due to assets or ops in the run failing. Set this to false if you only want to retry failures that occur due to the run worker crashing or unexpectedly terminating, and instead rely on op or asset-level retry policies to retry assert or op failures. Setting this field to false will only change retry behavior for runs on dagster version 1.6.7 or greater. <ul><li>**Default** - `0`</li></ul> |

### SSO default role

{/* dagster-plus/account/managing-users/managing-user-roles-permissions#user-permissions-reference */}
The `sso_default_role` setting lets you configure the default role on the deployment which is granted to new users that log in via SSO. For more information on available roles, see the [Dagster+ permissions reference](/todo.md).

```yaml
sso_default_role: EDITOR
```

| Property | Descripton |
| --- | --- |
| sso_default_role | If SAML SSO is enabled, this is the default role that will be assigned to Dagster+ users for this deployment. If SAML SSO is not enabled, this setting is ignored. <ul><li>**Default** - `Viewer`</li></ul> |

### Non-isolated runs

{/* /dagster-plus/deployment/serverless */}
Configure [non-isolated runs](/todo.md) on your deployment.

```yaml
non_isolated_runs:
  enabled: True
  max_concurrent_non_isolated_runs: 1
```

| Property | Descripton |
| --- | --- |
| enabled | If enabled, the `Isolate run environment` checkbox will appear in the Launchpad. <ul><li>**Default** - `true`</li></ul> |
| max_concurrent_non_isolated_runs | A limit for how many non-isolated runs to launch at once. Once this limit is reached, the checkbox will be greyed out and all runs will be isolated. This helps to avoid running out of RAM on the code location server. <ul><li>**Default** - `1`</li></ul> |