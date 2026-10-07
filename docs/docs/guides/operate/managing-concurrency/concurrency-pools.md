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

## Weight assets or ops within a pool with `pool_slots`

By default, every asset or op in a pool occupies exactly one slot while it executes. If the steps in a pool have very different resource footprints — for example, a memory-intensive export sharing a pool with lightweight database writes — a pool limit sized for the heaviest step leaves the pool underutilized whenever lighter steps run.

You can use the `pool_slots` keyword argument to specify how many of the pool's slots an asset or op occupies while it executes, similar to `pool_slots` in Airflow. For example, with a `database` pool limit of 4, a `pool_slots=3` asset executes alongside at most one default-weight asset, but three default-weight assets can execute together when it is not running:

<CodeExample
  path="docs_snippets/docs_snippets/guides/operate/managing_concurrency/pool_slots_concurrency.py"
  title="src/<project_name>/defs/assets.py"
  language="python"
/>

`pool_slots` defaults to `1`, must be a positive integer, and must not exceed the pool's limit — a step requesting more slots than the pool's limit will fail with an error rather than wait forever.

Steps waiting on a pool are granted slots in priority order, and a heavier step at the head of the queue is not overtaken by lighter steps queued behind it, even if they would fit in the currently available slots. This prevents a steady trickle of lightweight steps from starving a heavier step, at the cost of leaving some slots idle while the heavier step waits for its full slot count. Steps with a higher [priority](/deployment/execution/customizing-run-queue-priority) (set with the `dagster/priority` tag) are still granted slots first, regardless of weight.

:::note

`pool_slots` only applies to the default `op` pool granularity; with the pool granularity set to `run`, all runs are weighted equally.

:::

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

## Cleaning up concurrency slots from cancelled runs

:::warning

By default, Dagster does not automatically free concurrency pool slots when a run is cancelled or fails. If a run is cancelled while holding a concurrency slot, that slot remains occupied indefinitely, blocking future runs from claiming it. With a pool limit of 1, a single cancelled run will permanently deadlock all future runs for that pool.

:::

To prevent this, enable automatic slot cleanup by configuring `free_slots_after_run_end_seconds` in your [run monitoring settings](/deployment/execution/run-monitoring#freeing-concurrency-slots-after-run-completion):

```yaml
run_monitoring:
  enabled: true
  free_slots_after_run_end_seconds: 300
```

This setting is strongly recommended whenever you use concurrency pools. See [Troubleshooting concurrency issues](/guides/operate/managing-concurrency/troubleshooting-concurrency#runs-blocked-by-op-concurrency-limits-from-cancelled-runs) for recovery steps if you are already experiencing a deadlock.
