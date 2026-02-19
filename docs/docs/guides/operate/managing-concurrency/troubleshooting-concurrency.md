---
title: Troubleshooting concurrency issues
description: Troubleshooting common issues that arise when attempting to limit concurrency.
sidebar_position: 600
---

When limiting concurrency, you might run into issues until you get the configuration right.

## Runs going to STARTED status and skipping QUEUED

:::info
This only applies to Dagster Open Source.
:::

If you are running a version older than `1.10.0`, you may need to manually configure your deployment to enable run queueing by setting the `run_queue` key in your instance's settings. In the Dagster UI, navigate to **Deployment > Configuration** and verify that the `run_queue` key is set.

## Runs remaining in QUEUED status

The possible causes for runs remaining in `QUEUED` status depend on whether you're using Dagster+ or Dagster Open Source.

<Tabs>
  <TabItem value="Dagster+" label="Dagster+">
    If runs aren't being dequeued in Dagster+, the root causes could be:
    * **If using a [Hybrid deployment](/deployment/dagster-plus/hybrid)**, the agent serving the deployment may be down. In this situation, runs will be paused.
    * **Dagster+ is experiencing downtime**. For the latest on potential outages, check the [Dagster+ status page](https://dagstercloud.statuspage.io).

  </TabItem>
  <TabItem value="Dagster Open Source" label="Dagster Open Source">
  If runs aren't being dequeued in Dagster Open Source, the root cause is likely an issue with the Dagster daemon or the run queue configuration.

**Troubleshoot the Dagster daemon**

    * **Verify the Dagster daemon is set up and running.** In the Dagster UI, navigate to **Deployment > Daemons** and verify that the daemon is running. The **Run queue** should also be running. If you used [dagster dev](/guides/operate/webserver) to start the Dagster UI, the daemon should have been started for you. If the daemon isn't running, proceed to step 2.
    * **Verify the Dagster daemon can access the same storage as the Dagster webserver process.** Both the webserver process and the Dagster daemon should access the same storage, meaning they should use the same `dagster.yaml`. Locally, this means both processes should have the same set `DAGSTER_HOME` environment variable. If you used dagster dev to start the Dagster UI, both processes should be using the same storage. Refer to the [Dagster Instance docs](/deployment/oss/oss-instance-configuration) for more information.

**Troubleshoot the run queue configuration**<br />
If the daemon is running, runs may intentionally be left in the queue due to concurrency rules. To investigate:

    * **Check the output logged from the daemon process**, as this will include skipped runs.
    * **Check the max_concurrent_runs setting in your instance's dagster.yaml**. If set to 0, this may block the queue. You can check this setting in the Dagster UI by navigating to **Deployment > Configuration** and locating the `concurrency.runs.max_concurrent_runs` setting. For more information, see [Run queue limits](/guides/operate/managing-concurrency/run-queue-limits).
    * **Check the state of your run queue**. In some cases, the queue may be blocked by some number of in-progress runs. To view the status of your run queue, click **Runs** in the top navigation of the Dagster UI, then open the **Queued** and **In Progress** tabs. If there are queued or in-progress runs blocking the queue, you can terminate them to allow other runs to proceed.

  </TabItem>
</Tabs>
