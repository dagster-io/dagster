---
title: Dagster webserver and UI
description: The Dagster UI is a web-based interface for Dagster. You can inspect Dagster objects like assets, jobs, and schedules, and launch runs, view launched runs, and view assets produced by those runs.
sidebar_position: 20
---

The Dagster webserver serves the Dagster UI, a web-based interface for viewing and interacting with Dagster objects. It also responds to GraphQL queries.

In the UI, you can inspect Dagster objects (such as assets, jobs, schedules), launch runs, view launched runs, and view assets produced by those runs.

## Launching the webserver

The easiest way to launch the webserver from the command line during local development is to run:

```shell
dg dev
```

This command launches both the Dagster webserver and the [Dagster daemon](/deployment/execution/dagster-daemon), allowing you to start a full local deployment of Dagster from the command line.

The command will print out the URL you can access the UI from in the browser, usually on port 3000.

When invoked, the webserver will fetch definitions - such as assets, jobs, schedules, sensors, and resources - from a <PyObject section="definitions" module="dagster" object="Definitions" /> object in a Python module or package or the code locations configured in an open source deployment's [workspace files](/deployment/code-locations/workspace-yaml). For more information, see the [code locations documentation](/deployment/code-locations).

Note that several Dagster features, like schedules and sensors, require the Dagster daemon to be running in order to function.

## Dagster UI reference

### Overview page

The **Overview page**, also known as the "factory floor", provides a high-level look at the activity in your Dagster deployment, across all code locations. This includes information about runs, jobs, schedules, sensors, resources, and backfills, all of which can be accessed using the tabs on this page.

To access the overview page, click **Overview** in the top navigation bar.

![The Overview tab, also known as the Factory Floor, in the Dagster UI](/images/guides/operate/webserver/factory-floor.png)

### Assets

<Tabs>
<TabItem value="Asset catalog (OSS)">

The **Asset catalog** page lists all [assets](/guides/build/assets) in your Dagster deployment, which can be filtered by asset key, compute kind, asset group, [code location](/deployment/code-locations), and [tags](/guides/build/assets/metadata-and-tags/index.md#tags).

Clicking an asset opens the **Asset details** page for that asset. You can also navigate to the **Global asset lineage** page, reload definitions, and materialize assets.

To access the asset catalog page, click **Assets** in the top navigation bar.

![The Asset Catalog page in the Dagster UI](/images/guides/operate/webserver/asset-catalog.png)

</TabItem>
<TabItem value="Asset catalog (Dagster+ Pro)">

:::note

This feature is only available in Dagster+ Pro.

:::

The Dagster+ Pro **Asset catalog** page includes all the information and functionality of the original page, broken out by saved selections, asset group, kind, [owners](/guides/build/assets/metadata-and-tags/index.md#owners), [tags](/guides/build/assets/metadata-and-tags/index.md#tags), and [code location](/deployment/code-locations).

On this page, you can:

- View all [assets](/guides/build/assets) in your Dagster deployment
- View saved selections of assets
- Filter assets by asset key, asset group, code location, column, column tag, table name, kind, owner, and tag
- Access the global asset lineage page
- Reload definitions

To access this page, click **Catalog** in the top navigation bar:

![The Asset Catalog page in the Dagster UI](/images/guides/operate/webserver/asset-catalog-cloud-pro.png)

</TabItem>
<TabItem value="Asset selections (Dagster+)">

**[Asset selections](/guides/build/assets/asset-selection-syntax)** save a set of filters against the **Asset catalog** to show only the assets you want to see. You can share these views for easy access and faster team collaboration.

With **Asset selections**, you can:

- Select a scoped set of [assets](/guides/build/assets) in your Dagster deployment
- Create shared selections of assets for easier team collaboration

You can access asset selections by clicking **Catalog** in the top navigation, then clicking the **Saved selections** tab.

</TabItem>
<TabItem value="Global asset lineage">

The **Global asset lineage** page displays dependencies between all of the assets in your Dagster deployment, across all code locations.

On this page, you can:

- Filter assets by group
- Filter a subset of assets by using [asset selection syntax](/guides/build/assets/asset-selection-syntax)
- [Customize facets](/guides/build/assets/metadata-and-tags/asset-facets) displayed for each asset
- Reload definitions
- Materialize all or a selection of assets
- View run details for the latest materialization of any asset

- **Accessed by**:

  - **From the Asset catalog**: Clicking **View global asset lineage**, located near the top right corner of the page.
  - **From the Asset details page**: Clicking the **Lineage tab**.

![The Global asset lineage page in the Dagster UI](/images/guides/operate/webserver/global-asset-lineage.png)

</TabItem>
<TabItem value="Asset details">

The **Asset details** page contains details about a single asset. Use the tabs on this page to view detailed information about the asset:

- **Overview** - Information about the asset such as its description, resources, config, type, etc.
- **Partitions** - The asset's partitions, including their materialization status, metadata, and run information
- **Events** - The asset's materialization history
- **Checks** - The [Asset checks](/guides/test/asset-checks) defined for the asset
- **Lineage** - The asset's lineage in the **Global asset lineage** page
- **Automation** - The [Declarative Automation conditions](/guides/automate/declarative-automation) associated with the asset
- **Insights** - **Dagster+ only.** Historical information about the asset, such as failures and credit usage. Refer to the [Dagster+ Insights](/guides/observe/insights) documentation for more information.

To access the asset details page, click an asset in the **Asset catalog**.

![The Asset Details page in the Dagster UI](/images/guides/operate/webserver/asset-details.png)

</TabItem>
</Tabs>

### Runs

<Tabs>
<TabItem value="All runs">

The **Runs** page lists all job runs, which can be filtered by job name, run ID, execution status, or tag. Click a run ID to open the **Run details** page and view details for that run.

To access the runs page, click **Runs** in the top navigation bar.

![UI Runs page](/images/guides/operate/webserver/runs-page.png)

</TabItem>
<TabItem value="Run details">

The **Run details** page contains details about a single run, including timing information, errors, and logs. The upper left pane contains a Gantt chart, indicating how long each asset or op took to execute. The bottom pane displays filterable events and logs emitted during execution.

On this page, you can:

- **View structured event and raw compute logs.** Refer to the run logs tab for more info.
- **Re-execute a run** using the same configuration by clicking the **Re-execute** button. Related runs (e.g., runs created by re-executing the same previous run) are grouped in the right pane for easy reference

To access the run details page, click a run in the **Run details** page.

![UI Run details page](/images/guides/operate/webserver/run-details.png)

</TabItem>
<TabItem value="Run logs">

Located at the bottom of the **Run details** page, the **run logs** list every event that occurred in a run, the type of event, and detailed information about the event itself. There are two types of logs, which we'll discuss in the next section:

- Structured event logs
- Raw compute logs

To access the run logs, scroll to the bottom of the **Run details** page.

**Structured event logs**

- **Description**: Structured logs are enriched and categorized with metadata. For example, a label of which asset a log is about, links to an asset’s metadata, and what type of event it is available. This structuring also enables easier filtering and searching in the logs.

To access the structured event logs, click the **left side** of the toggle next to the log filter field.

![Structured event logs in the Run details page](/images/guides/operate/webserver/run-details-event-logs.png)

**Raw compute logs**

The raw compute logs contain logs for both [`stdout` and `stderr`](https://stackoverflow.com/questions/3385201/confused-about-stdin-stdout-and-stderr), which you can toggle between. To download the logs, click the **arrow icon** near the top right corner of the logs.

To access the raw compute logs, click the **right side** of the toggle next to the log filter field.

![Raw compute logs in the Run details page](/images/guides/operate/webserver/run-details-compute-logs.png)

</TabItem>
</Tabs>

### Schedules

<Tabs>
<TabItem value="All schedules">

The **Schedules** page lists all [schedules](/guides/automate/schedules) defined in your Dagster deployment, as well as information about upcoming ticks for anticipated scheduled runs. Click a schedule to open the **Schedule details** page.

To access the schedules page, click **Overview (top nav) > Schedules tab**.

![UI Schedules page](/images/guides/operate/webserver/schedules-tab.png)

</TabItem>
<TabItem value="Schedule details">

**Schedule details**

The **Schedule details** page contains details about a single schedule, including its next tick, tick history, and run history. Clicking the **Preview tick result** button near the top right corner of the page allows you to test the schedule.

To access the schedule details page, click a schedule in the **Schedules** page.

![UI Schedule details page](/images/guides/operate/webserver/schedule-details.png)

</TabItem>
</Tabs>

### Sensors

<Tabs>
<TabItem value="All sensors">

The **Sensors** page lists all [sensors](/guides/automate/sensors) defined in your Dagster deployment, as well as information about the sensor's frequency and its last tick. Click a sensor to view details about the sensor, including its recent tick history and recent runs.

To access the sensors page, click **Overview (top nav) > Sensors tab**.

![UI Sensors page](/images/guides/operate/webserver/sensors-tab.png)

</TabItem>
<TabItem value="Sensor details">

**Sensor details**

- **Description**: The **Sensor details** page contains details about a single sensor, including its next tick, tick history, and run history. Clicking the **Preview tick result** button near the top right corner of the page allows you to test the sensor.

To access sensor details, click a sensor on the **Sensors** page.

![UI Sensor details page](/images/guides/operate/webserver/sensor-details.png)

</TabItem>
</Tabs>

### Resources

<Tabs>
<TabItem value="All resources">

The **Resources** page lists all [resources](/guides/build/external-resources) defined in your Dagster deployment, across all code locations. Clicking a resource will open the **Resource details** page.

To access the resources page, click **Overview (top nav) > Resources tab**.

![UI Resources page](/images/guides/operate/webserver/resources-tab.png)

</TabItem>
<TabItem value="Resource details">

The **Resource details** page contains detailed information about a resource, including its configuration, description, and uses. Click the tabs below for more information about the tabs on this page.

To access the resource details page, click a resource on the **Resources** page.

<Tabs>
<TabItem value="Configuration tab">

The **Configuration** tab contains detailed information about a resource's configuration, including the name of each key, type, and value of each config value. If a key's value is an [environment variable](/guides/operate/configuration/using-environment-variables-and-secrets), an `Env var` badge will display next to the value.

To access the configuration tab, on the **Resource details** page, click the **Configuration tab**.

![UI Resource details - Configuration tab](/images/guides/operate/webserver/resource-details-configuration-tab.png)

</TabItem>
<TabItem value="Uses tab">

The **Uses** tab contains information about the other Dagster definitions that use the resource, including [assets](/guides/build/assets), [jobs](/guides/build/jobs), and [ops](/guides/build/ops). Clicking on any of these definitions will open the details page for that definition type.

To access the uses tab, on the **Resource details** page, click the **Uses tab**.

![UI Resource details - Uses tab](/images/guides/operate/webserver/resource-details-uses-tab.png)

</TabItem>
</Tabs>
</TabItem>
</Tabs>

### Backfills tab

The **Backfills** tab contains information about the backfills in your Dagster deployment, across all code locations. It includes information about when the partition was created, its target, status, run status, and more.

To access the backfills tab, click **Overview (top nav) > Backfills tab**.

![UI Backfills tab](/images/guides/operate/webserver/backfills-tab.png)

### Jobs

<Tabs>
<TabItem value="All jobs">

The **Jobs** page lists all [jobs](/guides/build/jobs) defined in your Dagster deployment across all code locations. It includes information about the job's schedule or sensor, its latest run time, and its history. Click a job to open the **Job details** page.

To access the jobs page, click **Overview (top nav) > Jobs tab**.

![UI Job Definition](/images/guides/operate/webserver/jobs-tab.png)

</TabItem>
<TabItem value="Job details">

The **Job details** page contains detailed information about a job. Click the tabs below for more information about the tabs on this page.

To access job details, click a job in the **Jobs** page.

<Tabs>
<TabItem value="Overview tab">

The **Overview** tab in the **Job details** page shows the graph of assets and/or ops that make up a job.

To access the overview tab, on the **Job details** page, click the **Overview** tab.

![UI Job Definition](/images/guides/operate/webserver/job-definition-with-ops.png)

</TabItem>
<TabItem value="Launchpad tab">

The **Launchpad tab** provides a configuration editor to let you experiment with configuration and launch runs. **Note**: For assets, this tab will only display if a job requires config. It displays by default for all op jobs.

To access the launchpad tab, on the **Job details** page, click the **Launchpad** tab.

![UI Launchpad](/images/guides/operate/webserver/job-config-with-ops.png)

</TabItem>
<TabItem value="Runs tab">

The **Runs** tab displays a list of recent runs for a job. Clicking a run will open the **Run details** page.

To access the runs tab, on the **Job details** page, click the **Runs** tab.

![UI Job runs tab](/images/guides/operate/webserver/jobs-runs-tab.png)

</TabItem>
<TabItem value="Partitions tab">

The **Partitions** tab displays information about the [partitions](/guides/build/partitions-and-backfills) associated with the job, including the total number of partitions, the number of missing partitions, and the job's backfill history.

:::note

This tab will display only if the job contains partitions.

:::

To access the partitions tab, on the **Job details** page, click the **Partitions** tab.

![UI Job Partitions tab](/images/guides/operate/webserver/jobs-partitions-tab.png)

</TabItem>
</Tabs>

</TabItem>
</Tabs>

### Deployment

The **Deployment** page includes information about the status of the code locations in your Dagster deployment, daemon (Open Source) or agent (Cloud) health, schedules, sensors, and configuration details.

<Tabs>
<TabItem value="Code locations tab">

The **Code locations** tab contains information about the code locations in your Dagster deployment, including their current status, when they were last updated, and high-level details about the definitions they contain.

You can reload Dagster definitions by:

- Clicking **Reload all** to reload all definitions in all code locations
- Clicking **Reload** next to a specific code location to reload only that code location's definitions

To access the code locations tab:

1. Click **Deployment** in the top navigation bar.
2. On the **Deployment overview** page, click the **Code locations** tab.

![UI Deployment overview page](/images/guides/operate/webserver/deployment-code-locations.png)

</TabItem>
<TabItem value="Open Source (OSS)">

In addition to the **Code locations** tab, Dagster OSS deployments contain a few additional tabs. For more information, see the tabs below.

<Tabs>
<TabItem value="Daemons tab">

The **Daemons** tab contains information about the [daemons](/deployment/execution/dagster-daemon) in an Open Source Dagster deployment, including their current status and when their last heartbeat was detected.

To access this tab, on the **Deployment overview** page, click **Daemons**.

![UI Deployment - Daemons tab](/images/guides/operate/webserver/deployment-daemons-tab.png)

</TabItem>
<TabItem value="Configuration tab">

The **Configuration** tab displays information about the configuration for a Dagster deployment, which is managed through the [`dagster.yaml`](/deployment/oss/dagster-yaml) file.

To access this tab, on the **Deployment overview** page, click the **Configuration** tab.

![UI Deployment - Configuration tab](/images/guides/operate/webserver/deployment-configuration-tab.png)

</TabItem>
</Tabs>
</TabItem>

<TabItem value="Dagster+">

In addition to the **Code locations** tab, Dagster+ deployments contain a few additional tabs. For more information, see the tabs below.

<Tabs>
<TabItem value="Agents tab">

The **Agents** tab contains information about the agents in a Dagster+ deployment.

To access this tab, on the **Deployment overview** page, click the **Agents** tab.

![UI Dagster+ Deployment - Agents tab](/images/guides/operate/webserver/deployment-cloud-agents-tab.png)

</TabItem>
<TabItem value="Environmental variables tab">

The **Environment variables** tab contains information about the environment variables configured in a Dagster+ deployment. For more information, see the [Dagster+ environment variables documentation](/deployment/dagster-plus/management/environment-variables).

To access this tab, on the **Deployment overview** page, click the **Environment variables** tab.

![UI Cloud Deployment - Environment variables tab](/images/guides/operate/webserver/deployment-cloud-environment-variables-tab.png)

</TabItem>
<TabItem value="Alerts tab">

The **Alerts** tab contains information about the alert policies configured for a Dagster+ deployment. For more information, see the [Dagster+ alerts documentation](/guides/observe/alerts).

To access this tab, on the **Deployment overview** page, click the **Alerts** tab.

![UI Dagster+ Deployment - Alerts tab](/images/guides/operate/webserver/deployment-cloud-alerts-tab.png)

</TabItem>
</Tabs>
</TabItem>
</Tabs>
