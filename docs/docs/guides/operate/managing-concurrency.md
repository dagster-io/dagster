---
title: 'Managing concurrency of Dagster assets, jobs, and Dagster instances'
sidebar_label: Managing concurrency
description: How to limit the number of runs a job, or assets for an instance of Dagster.
sidebar_position: 50
---

You often want to control the number of concurrent runs for a Dagster job, a specific asset, or for a type of asset or job. Limiting concurrency in your data pipelines can help prevent performance problems and downtime.

:::note

This article assumes familiarity with [assets](/guides/build/assets/) and [jobs](/guides/build/jobs/).

:::

## Limit the number of total runs that can be in progress at the same time

- Dagster Core, add the following to your [dagster.yaml](/guides/deploy/dagster-yaml)
- In Dagster+, add the following to your [deployment settings](/dagster-plus/deployment/management/deployments/deployment-settings-reference)

```yaml
concurrency:
  runs:
    max_concurrent_runs: 15
```

## Limit the number of assets or ops actively executing across all runs

You can assign assets and ops to concurrency pools which allow you to limit the number of in progress op executions across all runs. You first assign your asset or op to a concurrency pool using the `pool` keyword argument.

<CodeExample
  path="docs_snippets/docs_snippets/guides/operate/concurrency-pool-api.py"
  language="python"
  title="Specifying pools on assets and ops"
/>

You should be able to verify that you have set the pool correctly by viewing the details pane for the asset or op in the Dagster UI.

![Viewing the pool tag](/images/guides/operate/managing-concurrency/asset-pool-tag.png)

Once you have assigned your assets and ops to a concurrency pool, you can configure a pool limit for that pool in your deployment by using the Dagster UI or the Dagster CLI.

To specify a limit for the pool "database" using the UI, navigate to the `Deployments` &rarr; `Concurrency` settings page and click the `Add pool limit` button:

![Setting the pool limit](/images/guides/operate/managing-concurrency/add-pool-ui.png)

To specify a limit for the pool "database" using the CLI, use:

```
dagster instance concurrency set database 1
```

## Limit the number of runs that can be in progress for a set of ops

You can also use concurrency pools to limit the number of in progress runs containing those assets or ops. You can follow the steps in the [Limit the number of assets or ops actively in execution across all runs](#limit-the-number-of-assets-or-ops-actively-executing-across-all-runs) section to assign your assets and ops to pools and to configure the desired limit.

Once you have assigned your assets and ops to your pool, you can change your deployment settings to set the pool enforcement granularity. To limit the total number of runs containing a specific op at any given time (instead of the total number of ops actively executing), we need to set the pool granularity to `run`.

- Dagster Core, add the following to your [dagster.yaml](/guides/deploy/dagster-yaml)
- In Dagster+, add the following to your [deployment settings](/dagster-plus/deployment/management/deployments/deployment-settings-reference)

```yaml
concurrency:
  pools:
    granularity: 'run'
```

Without this granularity set, the default granularity is set to the `op`. This means that for a pool `foo` with a limit `1`, we enforce that only one op is executing at a given time across all runs, but the number of runs in progress is unaffected by the pool limit.

### Setting a default limit for concurrency pools

- Dagster+: Edit the `concurrency` config in deployment settings via the [Dagster+ UI](/guides/operate/webserver) or the [`dagster-cloud` CLI](/dagster-plus/deployment/management/dagster-cloud-cli/).
- Dagster Open Source: Use your instance's [dagster.yaml](/guides/deploy/dagster-yaml)

```yaml
concurrency:
  pools:
    default_limit: 1
```

## Limit the number of runs that can be in progress by run tag

You can also limit the number of in progress runs by run tag. This is useful for limiting sets of runs independent of which assets or ops it is executing. For example, you might want to limit the number of in-progress runs for a particular schedule. Or, you might want to limit the number of in-progress runs for all backfills.

```yaml
concurrency:
  runs:
    tag_concurrency_limits:
      - key: 'dagster/sensor_name'
        value: 'my_cool_sensor'
        limit: 5
      - key: 'dagster/backfill'
        limit: 10
```

### Limit the number of runs that can be in progress by unique tag value

To apply separate limits to each unique value of a run tag, set a limit for each unique value using `applyLimitPerUniqueValue`. For example, instead of limiting the number of backfill runs across all backfills, you may want to limit the number of runs for each backfill in progress:

```yaml
concurrency:
  runs:
    tag_concurrency_limits:
      - key: 'dagster/backfill'
        value:
          applyLimitPerUniqueValue: true
        limit: 10
```

## Limit the number of ops concurrently executing for a single run

While pool limits allow you to [limit the number of ops executing across all runs](#limit-the-number-of-assets-or-ops-actively-executing-across-all-runs), to limit the number of ops executing _within a single run_, you need to configure your [run executor](/guides/operate/run-executors). You can
limit concurrency for ops and assets in runs, by using `max_concurrent` in the run config, either in Python or using the Launchpad in the Dagster UI.

<CodeExample
  path="docs_snippets/docs_snippets/guides/operate/concurrency-run-scoped-op-concurrency.py"
  language="python"
  title="Limit concurrent op execution for a single run"
/>

The default limit for op execution within a run depends on which executor you are using. For example, the <PyObject section="execution" module="dagster" object="multiprocess_executor" /> by default limits the number of ops executing to the value of `multiprocessing.cpu_count()` in the launched run.

## Prevent runs from starting if another run is already occurring (advanced)

You can use Dagster's rich metadata to use a schedule or a sensor to only start a run when there are no currently running jobs.

<CodeExample
  path="docs_snippets/docs_snippets/guides/operate/concurrency-no-more-than-1-job.py"
  language="python"
  title="No more than 1 running job from a schedule"
/>

## Troubleshooting

When limiting concurrency, you might run into some issues until you get the configuration right.

### Runs going to STARTED status and skipping QUEUED

:::info
This only applies to Dagster Open Source.
:::

If you are running a version older than `1.10.0`, you may need to manually configure your deployment to enable run queueing by setting the `run_queue` key in your instance's settings. In the Dagster UI, navigate to **Deployment > Configuration** and verify that the `run_queue` key is set.

### Runs remaining in QUEUED status

The possible causes for runs remaining in `QUEUED` status depend on whether you're using Dagster+ or Dagster Open Source.

<Tabs>
  <TabItem value="Dagster+" label="Dagster+">
    If runs aren't being dequeued in Dagster+, the root causes could be:
    * **If using a [hybrid deployment](/dagster-plus/deployment/deployment-types/hybrid)**, the agent serving the deployment may be down. In this situation, runs will be paused.
    * **Dagster+ is experiencing downtime**. Check the [status page](https://dagstercloud.statuspage.io/) for the latest on potential outages.

  </TabItem>
  <TabItem value="Dagster Open Source" label="Dagster Open Source">
  If runs aren't being dequeued in Dagster Open Source, the root cause is likely an issue with the Dagster daemon or the run queue configuration.

**Troubleshoot the Dagster daemon**

    * **Verify the Dagster daemon is set up and running.** In the Dagster UI, navigate to **Deployment > Daemons** and verify that the daemon is running. The **Run queue** should also be running. If you used [dagster dev](/guides/operate/webserver) to start the Dagster UI, the daemon should have been started for you. If the daemon isn't running, proceed to step 2.
    * **Verify the Dagster daemon can access the same storage as the Dagster webserver process.** Both the webserver process and the Dagster daemon should access the same storage, meaning they should use the same `dagster.yaml`. Locally, this means both processes should have the same set `DAGSTER_HOME` environment variable. If you used dagster dev to start the Dagster UI, both processes should be using the same storage. Refer to the [Dagster Instance docs](/guides/deploy/dagster-instance-configuration) for more information.

**Troubleshoot the run queue configuration**
If the daemon is running, runs may intentionally be left in the queue due to concurrency rules. To investigate:
_ **Check the output logged from the daemon process**, as this will include skipped runs.
_ **Check the max_concurrent_runs setting in your instance's dagster.yaml**. If set to 0, this may block the queue. You can check this setting in the Dagster UI by navigating to Deployment > Configuration and locating the concurrency.runs.max_concurrent_runs setting. Refer to the [Limit the number of total runs that can be in progress at the same time](#limit-the-number-of-total-runs-that-can-be-in-progress-at-the-same-time) section for more info. \* **Check the state of your run queue**. In some cases, the queue may be blocked by some number of in-progress runs. To view the status of your run queue, click **Runs** in the top navigation of the Dagster UI and then open the **Queued** and **In Progress** tabs.

    If there are queued or in-progress runs blocking the queue, you can terminate them to allow other runs to proceed.

  </TabItem>
</Tabs>
