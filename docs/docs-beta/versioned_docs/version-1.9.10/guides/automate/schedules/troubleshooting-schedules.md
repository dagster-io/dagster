---
title: Troubleshooting schedules
sidebar_position: 700
---

If you have issues with a schedule, use the following steps to diagnose and resolve the problem.

## Step 1: Verify the schedule is included in the Definitions object

First, verify that the schedule has been included in a <PyObject section="definitions" module="dagster" object="Definitions" /> object. This ensures that the schedule is detectable and loadable by Dagster tools like the Dagster UI and CLI:

```python
defs = Definitions(
   assets=[asset_1, asset_2],
   jobs=[job_1],
   schedules=[all_assets_job_schedule],
)
```

For more information. see the [code locations documentation](/guides/deploy/code-locations/).

## Step 2: Verify that the schedule has been started

1. In the Dagster UI, click **Overview > Schedules tab**.
2. Locate the schedule. Schedules that have been started will have an enabled toggle in the **Running** column:

   ![Enabled toggle next to a schedule in the Schedules tab of the Overview page](/images/guides/automate/schedules/schedules-enabled-toggle.png)

## Step 3: Check for execution failures

Next, check that the schedule executed successfully. You can do this by looking at the **Last tick** column in the **Schedules tab**.

If the scheduled failed to execute, this column will contain a **Failed** badge. Click the badge to display the error and stack trace describing the failure.

## Step 4: Verify the schedule's interval configuration

Next, verify that the schedule is using the time interval you expect. In the **Schedules** tab, locate the schedule and look at the **Schedule** column:

![Highlighted Next tick value for a schedule in the Dagster UI](/images/guides/automate/schedules/schedules-next-tick.png)

The **Next tick** value indicates when the schedule is next expected to run. In the above image, the next tick is `May 2, 12:00 AM UTC`.

Verify that the time is what you expect, including the timezone.

## Step 5: Verify that the UI is using your latest Dagster code

The next step is to verify that the UI is using the latest version of your Dagster code. Use the tabs to view instructions for the version of Dagster you're using.

<Tabs>
<TabItem value="Local webserver or Dagster OSS">

1. In the UI, click **Settings** in the top navigation.
2. In the **Code locations** tab, click **Reload definitions** near the top right corner of the page.

</TabItem>
<TabItem value="Dagster+">

1. In the UI, click **Deployment** in the top navigation.
2. In the **Code locations** tab, locate the code location that contains the schedule definition.
3. Click **Redeploy**.

</TabItem>
</Tabs>

**If the code location can't be loaded** - for example, due to a syntax error - it will have a **Status** of **Failed**. Click the **View error** link in this column to view the error message.

**If the code location loaded successfully** but the schedule isn't present in the **Schedules** tab, the schedule may not be included in the code location's `Definitions` object. Refer to [Step 1](#step-1-verify-the-schedule-is-included-in-the-definitions-object) for more information.

## Step 6: Verify your dagster-daemon setup

:::note

This section is applicable to Open Source (OSS) deployments.

:::

If the schedule interval is correctly configured but runs aren't being created, it's possible that the dagster-daemon process isn't working correctly. If you haven't set up a Dagster daemon yet, refer to the [Open Source Deployment guides](/guides/deploy/deployment-options/) for more info.

### Verify the daemon is running

1. In the UI, click **Deployment** in the top navigation.
2. Click the **Daemons** tab.
3. Locate the **Scheduler** row.

The daemon process periodically sends out a hearbeat from the scheduler. If the scheduler daemon has a status of **Not running**, this indicates that there's an issue with your daemon deployment. If the daemon ran into an error that resulted in an exception, this error will often display in this tab.

If there isn't a clear error on this page or if the daemon should be sending heartbeats but isn't, move on to the next step.

### Check the daemon process logs

Next, check the logs from the daemon process. The steps to do this will depend on your deployment - for example, if you're using Kubernetes, you'll need to get the logs from the pod that's running the daemon. You should be able to search those logs for the name of the schedule (or `SchedulerDaemon` to see all logs associated with the scheduler) to gain an understanding of what's going wrong.

If the daemon output contains error indicating the schedule couldn't be found, verify that the daemon is using the same `workspace.yaml` file as the webserver. The daemon does not need to restart in order to pick up changes to the `workspace.yaml` file. Refer to the [Workspace files documentation](/guides/deploy/code-locations/workspace-yaml) for more information.

If the logs don't indicate the cause of the issue, move on to the next step.

### Check for execution failures

The last step is to check that the schedule executed successfully. If you didn't do this already, refer to [Step 3](#step-3-check-for-execution-failures) for more information.

## More help

**Still stuck?** If these steps didn't resolve the issue, reach out in [Slack](https://dagster.io/slack or [file an issue on GitHub](https://github.com/dagster-io/dagster/issues).

