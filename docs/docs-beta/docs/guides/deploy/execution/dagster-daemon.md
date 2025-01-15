---
title: "Dagster daemon"
sidebar_position: 100
---

Several Dagster features, like [schedules](/guides/automate/schedules/), [sensors](/guides/automate/sensors/), and [run queueing](/guides/deploy/execution/customizing-run-queue-priority), require a long-running `dagster-daemon` process to be included with your deployment.

## Starting the daemon

- [Running locally](#running-locally)
- [Deploying the daemon](#deploying-the-daemon)

### Running locally

<Tabs>
  <TabItem value="Running the daemon and webserver" label="Running the daemon and webserver">

The easiest way to run the Dagster daemon locally is to run the `dagster dev` command:

```shell
dagster dev
```

This command launches both the Dagster webserver and the Dagster daemon, allowing you to start a full local deployment of Dagster from the command line. For more information about `dagster dev`, see "[Running Dagster locally](/guides/deploy/deployment-options/running-dagster-locally).

  </TabItem>
  <TabItem value="Running only the daemon" label="Running only the daemon">

To run the Dagster daemon by itself:

```shell
dagster-daemon run
```

This command takes the same arguments as `dagster dev` for specifying where to find your code.

  </TabItem>
</Tabs>

### Deploying the daemon

For information on deploying the daemon to environments like Docker or Kubernetes, see the [deployment options documentation](/guides/deploy/deployment-options/).

## Available daemons

The `dagster-daemon` process reads from your [Dagster instance](/guides/deploy/dagster-instance-configuration) file to determine which daemons should be included. Each of the included daemons then runs on a regular interval in its own threads.

The following daemons are currently available:

|  Name                      | Description         | Enabled by       |
|----------------------------|---------------------|------------------|
| Scheduler daemon           |  Creates runs from active schedules   |  Enabled / runs as long as the default         <PyObject section="schedules-sensors" module="dagster._core.scheduler" object="DagsterDaemonScheduler"/> isn't overriden as the scheduler on your instance. |
| Run queue daemon           |  Launches queued runs, taking into account any limits and prioritization rules set on your instance |  Setting the [run coordinator](run-coordinators) on your instance <PyObject section="internals" module="dagster._core.run_coordinator" object="QueuedRunCoordinator" />.    |
| Sensor daemon |  Creates runs from active [sensors](/guides/automate/sensors/) that are turned on | Always enabled. |
| Run monitoring daemon      |  Handles [run worker](/guides/deploy/oss-deployment-architecture#job-execution-flow) failures |  Using the `run_monitoring` field in your instance. For more information, see "[Run monitoring](run-monitoring)".|

If the daemon is configured to use a [workspace file](/guides/deploy/code-locations/workspace-yaml) to load [code location(s)](/guides/deploy/code-locations/), note that they will periodically reload the file. This means that the `dagster-daemon` process doesn't need to be restarted when workspace files are changed.

## Checking daemon status in the Dagster UI

To check the status of the `dagster-daemon` process in the UI:

1. In the top navigation, click **Deployment**.
2. Click the **Daemons** tab.

This tab displays information about all the daemons currently configured on your instance.

Each daemon periodically writes a heartbeat to your instance storage. If a daemon doesn't show a recent heartbeat, check the logs from your `dagster-daemon` process for errors.
