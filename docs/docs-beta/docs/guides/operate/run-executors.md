---
title: Run executors
description: Executors are responsible for executing steps within a job run.
sidebar_position: 300
---

Executors are responsible for executing steps within a job run. Once a run has launched and the process for the run (the [run worker](/guides/deploy/oss-deployment-architecture#job-execution-flow)) is allocated and started, the executor assumes responsibility for execution.

Executors can range from single-process serial executors to managing per-step computational resources with a sophisticated control plane.

## Relevant APIs

| Name                                     | Description                                                                                  |
| ---------------------------------------- | -------------------------------------------------------------------------------------------- |
| <PyObject section="internals" module="dagster" object="executor" decorator /> | The decorator used to define executors. Defines an <PyObject section="internals" module="dagster" object="ExecutorDefinition" />. |
| <PyObject section="internals" module="dagster" object="ExecutorDefinition" /> | An executor definition.                                                                      |

## Specifying executors

- [Directly on jobs](#directly-on-jobs)
- [For a code location](#for-a-code-location)

### Directly on jobs

Every job has an executor. The default executor is the <PyObject section="execution" module="dagster" object="multi_or_in_process_executor" />, which by default executes each step in its own process. This executor can be configured to execute each step within the same process.

An executor can be specified directly on a job by supplying an <PyObject section="internals" module="dagster" object="ExecutorDefinition" /> to the `executor_def` parameter of <PyObject section="jobs" module="dagster" object="job" decorator /> or <PyObject section="graphs" module="dagster" object="GraphDefinition" method="to_job" />:

{/* TODO convert to <CodeExample> */}
```python file=/deploying/executors/executors.py startafter=start_executor_on_job endbefore=end_executor_on_job
from dagster import graph, job, multiprocess_executor


# Providing an executor using the job decorator
@job(executor_def=multiprocess_executor)
def the_job(): ...


@graph
def the_graph(): ...


# Providing an executor using graph_def.to_job(...)
other_job = the_graph.to_job(executor_def=multiprocess_executor)
```

### For a code location

To specify a default executor for all jobs and assets provided to a code location, supply the `executor` argument to the <PyObject section="definitions" module="dagster" object="Definitions" /> object.

If a job explicitly specifies an executor, then that executor will be used. Otherwise, jobs that don't specify an executor will use the default provided to the code location:

{/* TODO convert to <CodeExample> */}
```python file=/deploying/executors/executors.py startafter=start_executor_on_repo endbefore=end_executor_on_repo
from dagster import multiprocess_executor, define_asset_job, asset, Definitions


@asset
def the_asset():
    pass


asset_job = define_asset_job("the_job", selection="*")


@job
def op_job(): ...


# op_job and asset_job will both use the multiprocess_executor,
# since neither define their own executor.

defs = Definitions(
    assets=[the_asset], jobs=[asset_job, op_job], executor=multiprocess_executor
)
```

:::note

Executing a job via <PyObject section="jobs" module="dagster" object="JobDefinition" method="execute_in_process" /> overrides the job's executor and uses <PyObject section="execution" module="dagster" object="in_process_executor" /> instead.

:::

## Example executors

| Name | Description |
|------|-------------|
| <PyObject section="execution" module="dagster" object="in_process_executor" /> | Execution plan executes serially within the run worker itself. |
| <PyObject section="execution" module="dagster" object="multiprocess_executor" /> | Executes each step within its own spawned process. Has a configurable level of parallelism. |
| <PyObject section="libraries" module="dagster_dask" object="dask_executor" /> | Executes each step within a Dask task. |
| <PyObject section="libraries" module="dagster_celery" object="celery_executor" /> | Executes each step within a Celery task. |
| <PyObject section="libraries" module="dagster_docker" object="docker_executor" /> | Executes each step within an ephemeral Kubernetes pod. |
| <PyObject section="libraries" module="dagster_k8s" object="k8s_job_executor" /> | Executes each step within an ephemeral Kubernetes pod. |
| <PyObject section="libraries" module="dagster_celery_k8s" object="celery_k8s_job_executor" /> | Executes each step within a ephemeral Kubernetes pod, using Celery as a control plane for prioritization and queuing. |
| <PyObject section="libraries" module="dagster_celery_docker" object="celery_docker_executor" /> | Executes each step within a Docker container, using Celery as a control plane for prioritization and queueing. |

## Custom executors

The executor system is pluggable, meaning it's possible to write your own executor to target a different execution substrate. Note that this is not currently well-documented and the internal APIs continue to be in flux.
