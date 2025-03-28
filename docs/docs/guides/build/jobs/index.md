---
title: Jobs
description: Jobs are the main unit of execution and monitoring in Dagster.
sidebar_position: 90
---

Jobs are the main unit of execution and monitoring in Dagster. They allow you to execute a portion of a graph of [asset definitions](https://docs.dagster.io/guides/build/assets/defining-assets) or [ops](https://docs.dagster.io/guides/build/ops/) based on a schedule or an external trigger.

When a job begins, it kicks off a run. A run is a single execution of a job in Dagster. Runs can be launched and viewed in the [Dagster UI](https://docs.dagster.io/guides/operate/webserver#dagster-ui-reference).

## Benefits

Using jobs provides the following benefits:

- **Automation**: With [schedules](https://docs.dagster.io/guides/automate/schedules/) and [sensors](https://docs.dagster.io/guides/automate/sensors/), jobs can be used to automate the execution of your Dagster pipelines. Refer to the [Automation guide](https://docs.dagster.io/guides/automate/) for more info.
- **Control job run priority**: If using a [run queue](https://docs.dagster.io/guides/deploy/execution/run-coordinators), you can apply custom prioritization rules to how job runs are prioritized and executed.
- **Potential for improved efficency**: By applying concurrency limits to job runs, there may be benefits to your pipeline's efficiency. Refer to the [Managing concurrency guide](https://docs.dagster.io/guides/operate/managing-concurrency) for more info and examples.

## Uses

Jobs are supported for both asset definitions and ops, but the usage for each concept is unique. Refer to the following documentation for more info:

- [Asset jobs](https://docs.dagster.io/guides/build/jobs/asset-jobs)
- [Op jobs](https://docs.dagster.io/guides/build/jobs/op-jobs)

With jobs, you can:

- Automate the execution of [asset definitions](https://docs.dagster.io/guides/build/assets/defining-assets) and [ops](https://docs.dagster.io/guides/build/ops/)
- Materialize a selection of assets based on a schedule or external trigger (sensor)
- Attach information using [metadata](https://docs.dagster.io/guides/build/assets/metadata-and-tags) and [tags](https://docs.dagster.io/guides/build/assets/metadata-and-tags/tags)
- View and launch runs of jobs in the [Dagster UI](https://docs.dagster.io/guides/operate/webserver#dagster-ui-reference)
