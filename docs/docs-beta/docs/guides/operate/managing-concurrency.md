---
title: "Managing concurrency of Dagster assets, jobs, and Dagster instances"
sidebar_label: Managing concurrency
description: How to limit the number of runs a job, or assets for an instance of Dagster.
sidebar_position: 200
---

You often want to control the number of concurrent runs for a Dagster job, a specific asset, or for a type of asset or job. Limiting concurrency in your data pipelines can help prevent performance problems and downtime.


:::note

This article assumes familiarity with [assets](/guides/build/assets/) and [jobs](/guides/build/assets/asset-jobs)

:::

## Limit how many jobs can be running at the same time


* Dagster Core, add the following to your [dagster.yaml](/guides/deploy/dagster-yaml)
* In Dagster+, add the following to your [deployment settings](/dagster-plus/deployment/management/settings/deployment-settings)

```yaml
run_queue:
  max_concurrent_runs: 15
```


<CodeExample filePath="guides/tbd/concurrency-global.py" language="python" title="Global concurrency limits" />

## Limit how many ops or assets can be running at the same time

You can control the number of assets or ops that are running concurrently within a job using the `config` argument of `dg.define_asset_job()` or `dg.@job()` for ops.

<Tabs>
  <TabItem value="Assets" label="Asset job">
    <CodeExample filePath="guides/tbd/concurrency-job-asset.py" language="python" title="Asset concurrency limits in a job" />

  </TabItem>

  <TabItem value="Ops" label="Op job">
    <CodeExample filePath="guides/tbd/concurrency-job-op.py" language="python" title="Op concurrency limits in a job" />

  </TabItem>
</Tabs>


## Limit how many of a certain type of op or asset can run across all runs

You can a limit for all ops or assets with a specific tag key or key-value pair. Ops or assets above that limit will be queued. Use `tag_concurrency_limits` in the job's config, either in Python or using the Launchpad in the Dagster UI.

For example, you might want to limit the number of ops or assets that are running with a key of `database` across all runs (to limit the load on that database).

:::warning
This feature is experimental and is only supported with Postgres/MySQL storage.
:::


```yaml
# dagster.yaml for Dagster Core; Deployment Settings for Dagster+
run_coordinator:
  module: dagster.core.run_coordinator
  class: QueuedRunCoordinator
  config:
    tag_concurrency_limits:
      - key: "dagster/concurrency_key"
        value: "database"
        limit: 1
```

To specify a global concurrency limit using the CLI, use:

```
dagster instance concurrency set database 1
```

A default concurrency limit can be configured for the instance, for any concurrency keys that don't have an explicit limit set:

* Dagster+: Use the Dagster+ UI or the dagster-cloud CLI
* Dagster Open Source: Use your instance's dagster.yaml

To enable this default value, use `concurrency.default_op_concurrency_limit`. For example, the following would set the default concurrency value for the deployment to 1:
```yaml
concurrency:
  default_op_concurrency_limit: 1
```

<Tabs>
  <TabItem value="Asset Tag" label="Asset tag concurrency limits">
    <CodeExample filePath="guides/tbd/concurrency-tag-key-asset.py" language="python" title="No more than 1 asset running with a tag of 'database' across all runs" />

  </TabItem>
  <TabItem value="Op Tag" label="Op tag concurrency limits">
  <CodeExample filePath="guides/tbd/concurrency-tag-key-op.py" language="python" title="No more than 1 op running with a tag of 'database' across all runs" />

  </TabItem>
</Tabs>

You can also limit concurrency for a tag within the job definition, for example to limit the number of specific assets running at the same time *within* that run.

<Tabs>
  <TabItem value="Asset Tag with Job" label="Asset tag concurrency limits in a run">
    <CodeExample filePath="guides/tbd/concurrency-tag-key-job-asset.py" language="python" title="No more than 1 asset running with a tag of 'database' within a run" />

  </TabItem>
  <TabItem value="Op Tag with Job" label="Op tag concurrency limits in a run">
  <CodeExample filePath="guides/tbd/concurrency-tag-key-job-op.py" language="python" title="No more than 1 op running with a tag of 'database' within a run" />
  </TabItem>
</Tabs>


## Override job level concurrency in the Launchpad

You can override the default job-level settings, such as the value of the `max_concurrent` key for a job, by launching a job in the Launchpad in the Dagster UI.

Need screenshot here

## Prevent runs from starting if another run is already occurring (advanced)

You can use Dagster's rich metadata to use a schedule or a sensor to only start a run when there are no currently running jobs.

{/* TODO fix this code example */}
<CodeExample filePath="guides/tbd/concurrency-no-more-than-1-job.py" language="python" title="No more than 1 running job from a schedule" />


## Troubleshooting

When limiting concurrency, you might run into some issues until you get the configuration right.

### Runs going to STARTED status and skipping QUEUED

:::info
This only applies to Dagster Open Source.
:::

The `run_queue` key may not be set in your instance's settings. In the Dagster UI, navigate to Deployment > Configuration and verify that the `run_queue` key is set.

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

    * **Verify the Dagster daemon is set up and running.** In the Dagster UI, navigate to **Deployment > Daemons** and verify that the daemon is running. The **Run queue** should also be running. If you used [dagster dev](/guides/deploy/execution/webserver) to start the Dagster UI, the daemon should have been started for you. If the daemon isn't running, proceed to step 2.
    * **Verify the Dagster daemon can access the same storage as the Dagster webserver process.** Both the webserver process and the Dagster daemon should access the same storage, meaning they should use the same `dagster.yaml`. Locally, this means both processes should have the same set `DAGSTER_HOME` environment variable. If you used dagster dev to start the Dagster UI, both processes should be using the same storage. Refer to the [Dagster Instance docs](/todo) for more information.

  **Troubleshoot the run queue configuration**
    If the daemon is running, runs may intentionally be left in the queue due to concurrency rules. To investigate:
    * **Check the output logged from the daemon process**, as this will include skipped runs.
    * **Check the max_concurrent_runs setting in your instance's dagster.yaml**. If set to 0, this may block the queue. You can check this setting in the Dagster UI by navigating to Deployment > Configuration and locating the run_queue.max_concurrent_runs setting. Refer to the Limiting overall runs section for more info.
    * **Check the state of your run queue**. In some cases, the queue may be blocked by some number of in-progress runs. To view the status of your run queue, click **Runs** in the top navigation of the Dagster UI and then open the **Queued** and **In Progress** tabs.
    
    If there are queued or in-progress runs blocking the queue, you can terminate them to allow other runs to proceed.
  </TabItem>
</Tabs>
