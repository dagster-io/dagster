---
title: "Run coordinators"
sidebar_position: 300
---

In production Dagster deployments, there are often many runs being launched at once. The _run coordinator_ lets you control the policy that Dagster uses to manage the set of runs in your deployment.

When you submit a run from the Dagster UI or the Dagster command line, it’s first sent to the run coordinator, which applies any limits or prioritization policies before eventually sending it to the [run launcher](run-launchers) to be launched.

## Run coordinator types

The following run coordinators can be configured on your [Dagster instance](/guides/deploy/dagster-instance-configuration):

| Term | Definition |
|------|------------|
| <PyObject section="internals" module="dagster._core.run_coordinator" object="DefaultRunCoordinator"/> | The `DefaultRunCoordinator` calls launch_run on the instance’s run launcher immediately in the same process, without applying any limits or prioritization rules.<br />When this coordinator is set, clicking **Launch Run** in the Dagster UI will immediately launch the run from the Dagster daemon process. Similarly, scheduled runs will immediately launch from the scheduler process. |
| <PyObject section="internals" module="dagster._core.run_coordinator" object="QueuedRunCoordinator"/> | The `QueuedRunCoordinator` sends runs to the Dagster daemon via a run queue. The daemon pulls runs from the queue and calls launch_run on submitted runs.<br/>Using this run coordinator enables instance-level limits on run concurrency, as well as custom run prioritization rules. |

## Configuring run coordinators

If you opt to use the `DefaultRunCoordinator`, no configuration is required on your part.

However, if using the `QueuedRunCoordinator` or building a custom implementation, you can define [custom run prioritization rules](customizing-run-queue-priority) and [instance-level concurrency limits](/guides/operate/managing-concurrency).
