---
title: Jobs
description: Jobs are the main unit of execution and monitoring in Dagster.
sidebar_position: 90
---

Jobs are the main unit of execution and monitoring in Dagster. They allow you to execute a portion of a graph of [asset definitions](/guides/build/assets/defining-assets) or [ops](/guides/build/ops/) based on a schedule or an external trigger.

When a job begins, it kicks off a run. A run is a single execution of a job in Dagster. Runs can be launched and viewed in the [Dagster UI](/guides/operate/webserver#dagster-ui-reference).

## Benefits

Using jobs provides the following benefits:

- **Automation**: With [schedules](/guides/automate/schedules/) and [sensors](/guides/automate/sensors/), jobs can be used to automate the execution of your Dagster pipelines. Refer to the [Automation guide](/guides/automate/) for more info.
- **Control job run priority**: If using a [run queue](/guides/deploy/execution/run-coordinators), you can apply custom prioritization rules to how job runs are prioritized and executed.
- **Potential for improved efficency**: By applying concurrency limits to job runs, there may be benefits to your pipeline's efficiency. Refer to the [Managing concurrency guide](/guides/operate/managing-concurrency) for more info and examples.

## Uses

Jobs are supported for both asset definitions and ops, but the usage for each concept is unique. Refer to the following documentation for more info:

- [Asset jobs](/guides/build/jobs/asset-jobs)
- [Op jobs](/guides/build/jobs/op-jobs)

With jobs, you can:

- Automate the execution of [asset definitions](/guides/build/assets/defining-assets) and [ops](/guides/build/ops/)
- Materialize a selection of assets based on a schedule or external trigger (sensor)
- Attach information using [metadata](/guides/build/assets/metadata-and-tags) and [tags](/guides/build/assets/metadata-and-tags/tags)
- View and launch runs of jobs in the [Dagster UI](/guides/operate/webserver#dagster-ui-reference)
