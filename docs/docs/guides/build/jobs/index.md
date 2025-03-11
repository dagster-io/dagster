---
title: Op jobs
description: Jobs are the main unit of execution and monitoring in Dagster.
---

Jobs are the main unit of execution and monitoring in Dagster. They allow you to execute a portion of a graph of [asset definitions](/concepts/assets/software-defined-assets) or [ops](/concepts/ops-jobs-graphs/ops) based on a schedule or an external trigger.

When a job begins, it kicks off a run. A run is a single execution of a job in Dagster. Runs can be launched and viewed in the [Dagster UI](/guides/operate/webserver#dagster-ui-reference).

## Benefits

Using jobs provides the following benefits:

- **Automation**: With [schedules](/concepts/automation/schedules) and [sensors](/concepts/partitions-schedules-sensors/sensors), jobs can be used to automate the execution of your Dagster pipelines. Refer to the [Automation guide](/concepts/automation) for more info.
- **Control job run priority**: If using a [run queue](/deployment/run-coordinator), you can apply custom prioritization rules to how job runs are prioritized and executed.
- **Potential for improved efficency**: By applying concurrency limits to job runs, there may be benefits to your pipeline's efficiency. Refer to the [Limiting run concurrency guide](/guides/limiting-concurrency-in-data-pipelines) for more info and examples.

## Uses

Jobs are supported for both asset definitions and ops, but the usage for each concept is unique. Refer to the following documentation for more info:

- [Asset jobs](/concepts/assets/asset-jobs)
- [Op jobs](/concepts/ops-jobs-graphs/op-jobs)

With jobs, you can:

- Automate the execution of [asset definitions](/concepts/assets/software-defined-assets) and [ops](/concepts/ops-jobs-graphs/ops)
- Materialize a selection of assets based on a schedule or external trigger (sensor)
- Attach information using [metadata](/concepts/metadata-tags) and [tags](/concepts/metadata-tags/tags)
- View and launch runs of jobs in the [Dagster UI](/concepts/webserver/ui)
