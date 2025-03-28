---
title: Job execution
description: Dagster provides several methods to execute jobs.
sidebar_position: 300
---

:::note

This guide is applicable to both [ops](/guides/build/ops/) and [jobs](/guides/build/jobs/)

:::

Dagster provides several methods to execute [op](/guides/build/jobs/op-jobs) and [asset jobs](/guides/build/jobs/asset-jobs). This guide explains different ways to do one-off execution of jobs using the Dagster UI, command line, or Python APIs.

You can also launch jobs in other ways:

- [Schedules](/guides/automate/schedules/) can be used to launch runs on a fixed interval.
- [Sensors](/guides/automate/sensors/) allow you to launch runs based on external state changes.

## Relevant APIs

| Name                                                            | Description                                                                        |
| --------------------------------------------------------------- | ---------------------------------------------------------------------------------- |
| <PyObject section="jobs" module="dagster" object="JobDefinition.execute_in_process" /> | A method to execute a job synchronously, typically for running scripts or testing. |

## Executing a job

Dagster supports the following methods to execute one-off jobs. Click the tabs for more info.

<Tabs>
<TabItem value="Dagster UI">

Using the Dagster UI, you can view, interact, and execute jobs.

To view your job in the UI, use the [`dagster dev`](/api/python-api/cli#dagster-dev) command:

```bash
dagster dev -f my_job.py
```

Then navigate to `http://localhost:3000`:

![Pipeline def](/images/guides/build/ops/pipeline-def.png)

Click on the **Launchpad** tab, then press the **Launch Run** button to execute the job:

![Job run](/images/guides/build/ops/pipeline-run.png)

By default, Dagster will run the job using the <PyObject section="execution" module="dagster" object="multiprocess_executor" /> - that means each step in the job runs in its own process, and steps that don't depend on each other can run in parallel.

The Launchpad also offers a configuration editor to let you interactively build up the configuration. Refer to the [run configuration documentation](/guides/operate/configuration/run-configuration#specifying-runtime-configuration) for more info.

</TabItem>
<TabItem value="Command line">

The dagster CLI includes the following commands for job execution:

- [`dagster job execute`](/api/python-api/cli#dagster-job) for direct execution
- [`dagster job launch`](/api/python-api/cli#dagster-job) for launching runs asynchronously using the [run launcher](/guides/deploy/execution/run-launchers) on your instance

To execute your job directly, run:

```bash
dagster job execute -f my_job.py
```

</TabItem>
<TabItem value="Python">

### Python APIs

Dagster includes Python APIs for execution that are useful when writing tests or scripts.

<PyObject section="jobs" module="dagster" object="JobDefinition.execute_in_process" /> executes a job and
returns an <PyObject section="execution" module="dagster" object="ExecuteInProcessResult" />.

<CodeExample path="docs_snippets/docs_snippets/concepts/ops_jobs_graphs/job_execution.py" startAfter="start_execute_marker" endBefore="end_execute_marker" />

You can find the full API documentation in [Execution API](/api/python-api/execution) and learn more about the testing use cases in the [testing documentation](/guides/test/).

</TabItem>
</Tabs>

## Executing job subsets

Dagster supports ways to run a subset of a job, called **op selection**.

### Op selection syntax

To specify op selection, Dagster supports a simple query syntax.

It works as follows:

- A query includes a list of clauses.
- A clause can be an op name, in which case that op is selected.
- A clause can be an op name preceded by `*`, in which case that op and all of its ancestors (upstream dependencies) are selected.
- A clause can be an op name followed by `*`, in which case that op and all of its descendants (downstream dependencies) are selected.
- A clause can be an op name followed by any number of `+`s, in which case that op and descendants up to that many hops away are selected.
- A clause can be an op name preceded by any number of `+`s, in which case that op and ancestors up to that many hops away are selected.

Let's take a look at some examples:

| Example      | Description                                                                                         |
| ------------ | --------------------------------------------------------------------------------------------------- |
| `some_op`    | Select `some_op`                                                                                    |
| `*some_op`   | Select `some_op` and all ancestors (upstream dependencies).                                         |
| `some_op*`   | Select `some_op` and all descendants (downstream dependencies).                                     |
| `*some_op*`  | Select `some_op` and all of its ancestors and descendants.                                          |
| `+some_op`   | Select `some_op` and its direct parents.                                                            |
| `some_op+++` | Select `some_op` and its children, its children's children, and its children's children's children. |

### Specifying op selection

Use this selection syntax in the `op_selection` argument to the <PyObject section="jobs" module="dagster" object="JobDefinition.execute_in_process" />:

<CodeExample path="docs_snippets/docs_snippets/concepts/ops_jobs_graphs/job_execution.py" startAfter="start_op_selection_marker" endBefore="end_op_selection_marker" />

Similarly, you can specify the same op selection in the Dagster UI Launchpad:

![Op selection](/images/guides/build/ops/solid-selection.png)

## Controlling job execution

Each <PyObject section="jobs" module="dagster" object="JobDefinition" /> contains an <PyObject section="internals" module="dagster" object="ExecutorDefinition" /> that determines how it will be executed.

This `executor_def` property can be set to allow for different types of isolation and parallelism, ranging from executing all the ops in the same process to executing each op in its own Kubernetes pod. See [Executors](/guides/operate/run-executors) for more details.

### Default job executor

The default job executor definition defaults to multiprocess execution. It also allows you to toggle between in-process and multiprocess execution via config.

Below is an example of run config as YAML you could provide in the Dagster UI playground to launch an in-process execution.

<CodeExample path="docs_snippets/docs_snippets/concepts/ops_jobs_graphs/job_execution.py" startAfter="start_ip_yaml" endBefore="end_ip_yaml" />

Additional config options are available for multiprocess execution that can help with performance. This includes limiting the max concurrent subprocesses and controlling how those subprocesses are spawned.

The example below sets the run config directly on the job to explicitly set the max concurrent subprocesses to `4`, and change the subprocess start method to use a forkserver.

<CodeExample path="docs_snippets/docs_snippets/concepts/ops_jobs_graphs/job_execution.py" startAfter="start_mp_cfg" endBefore="end_mp_cfg" />

Using a forkserver is a great way to reduce per-process overhead during multiprocess execution, but can cause issues with certain libraries. Refer to the [Python documentation](https://docs.python.org/3/library/multiprocessing.html#contexts-and-start-methods) for more info.

#### Op concurrency limits

In addition to the `max_concurrent` limit, you can use `tag_concurrency_limits` to specify limits on the number of ops with certain tags that can execute at once within a single run.

Limits can be specified for all ops with a certain tag key or key-value pair. If any limit would be exceeded by launching an op, then the op will stay queued. Asset jobs will look at the `op_tags` field on each asset in the job when checking them for tag concurrency limits.

For example, the following job will execute at most two ops at once with the `database` tag equal to `redshift`, while also ensuring that at most four ops execute at once:

<CodeExample path="docs_snippets/docs_snippets/concepts/ops_jobs_graphs/job_execution.py" startAfter="start_tag_concurrency" endBefore="end_tag_concurrency" />

:::note

These limits are only applied on a per-run basis. You can apply op concurrency limits across multiple runs using the <PyObject section="libraries" module="dagster_celery" object="celery_executor" /> or <PyObject section="libraries" module="dagster_celery_k8s" object="celery_k8s_job_executor" />.

Refer to the [Managing concurrency in data pipelines guide](/guides/operate/managing-concurrency) for more info about op concurrency, and how to limit run concurrency.

:::