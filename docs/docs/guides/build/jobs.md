---
title: "Jobs"
sidebar_position: 200
---

Jobs are the main unit of execution and monitoring in Dagster. They allow you to execute a portion of a graph of [asset definitions](/guides/build/assets/defining-assets) or [ops](/guides/build/ops) based on a schedule or an external trigger.

When a job begins, it kicks off a _run_. A run is a single execution of a job in Dagster. Runs can be launched and viewed in the Dagster UI.

## Benefits

With jobs, you can

* View and launch runs of jobs in the Dagster UI
* Automate the execution of your Dagster pipelines with [schedules](/guides/automate/schedules/) and [sensors](/guides/automate/sensors/).
* Attach information using [metadata and tags](/guides/build/assets/metadata-and-tags)
* Apply custom prioritization rules to how job runs are prioritized and executed if you are using a [run queue](/guides/deploy/execution/run-coordinators)
* Make your pipelines more efficient if you apply concurrency limits to job runs. For more information, see "[Managing concurrency of Dagster assets, jobs, and Dagster instances](/guides/operate/managing-concurrency)".
