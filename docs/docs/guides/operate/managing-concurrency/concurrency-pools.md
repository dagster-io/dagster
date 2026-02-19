---
title: Concurrency pools
description: Using concurrency pools to limit the number of assets or ops executing across runs, or limit the number of runs in progress for a set of ops.
sidebar_position: 200
---

## Setting a default limit for concurrency pools

- Dagster+: Edit the `concurrency` config in deployment settings via the [Dagster+ UI](/guides/operate/webserver) or the [`dagster-cloud` CLI](/api/clis/dagster-cloud-cli).
- Dagster Open Source: Use your instance's [dagster.yaml](/deployment/oss/dagster-yaml)

```yaml
concurrency:
  pools:
    default_limit: 1
```

## Limit the number of assets or ops actively executing across all runs

You can assign assets and ops to concurrency pools which allow you to limit the number of in progress op executions across all runs. This is ideal for protecting shared resources like databases or APIs. You first assign your asset or op to a concurrency pool using the `pool` keyword argument.

<CodeExample
  path="docs_snippets/docs_snippets/guides/operate/managing_concurrency/pool_concurrency.py"
  title="src/<project_name>/defs/assets.py"
  language="python"
/>

You should be able to verify that you have set the pool correctly by viewing the details pane for the asset or op in the Dagster UI.

![Viewing the pool tag](/images/guides/operate/managing-concurrency/asset-pool-tag.png)

Once you have assigned your assets and ops to a concurrency pool, you can configure a pool limit for that pool in your deployment by using the [Dagster UI](/guides/operate/webserver) or the [`dagster` CLI](/api/clis/cli).

To specify a limit for the pool "database" using the UI, navigate to the `Deployments` &rarr; `Concurrency` settings page and click the `Add pool limit` button:

![Setting the pool limit](/images/guides/operate/managing-concurrency/add-pool-ui.png)

To specify a limit for the pool "database" using the `dagster` CLI, use:

```
dagster instance concurrency set database 1
```

## Limit the number of runs that can be in progress for a set of ops

You can also use concurrency pools to limit the number of in progress runs containing those assets or ops. You can follow the steps in the [Limit the number of assets or ops actively in execution across all runs](#limit-the-number-of-assets-or-ops-actively-executing-across-all-runs) section to assign your assets and ops to pools and to configure the desired limit.

Once you have assigned your assets and ops to your pool, you can change your deployment settings to set the pool enforcement granularity. To limit the total number of runs containing a specific op at any given time (instead of the total number of ops actively executing), we need to set the pool granularity to `run`.

- Dagster Core, add the following to your [dagster.yaml](/deployment/oss/dagster-yaml)
- In Dagster+, add the following to your [deployment settings](/deployment/dagster-plus/deploying-code/full-deployments/full-deployment-settings-reference)

```yaml
concurrency:
  pools:
    granularity: 'run'
```

Without this granularity set, the default granularity is set to the `op`. This means that for a pool `foo` with a limit `1`, we enforce that only one op is executing at a given time across all runs, but the number of runs in progress is unaffected by the pool limit.
