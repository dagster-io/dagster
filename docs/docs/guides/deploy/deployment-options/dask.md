---
title: 'Executing on Dask'
description: The dask_executor uses Dask to execute Dagster ops.
---

The [dagster-dask](/api/python-api/libraries/dagster-dask) module makes a **`dask_executor`** available, which can target either a local Dask cluster or a distributed cluster. Computation is distributed across the cluster at the execution step level -- that is, we use Dask to orchestrate execution of the steps in a job, not to parallelize computation within those steps.

This executor takes the compiled execution plan, and converts each execution step into a [Dask Future](https://docs.dask.org/en/latest/futures.html) configured with the appropriate task dependencies to ensure tasks are properly sequenced. When the job is executed, these futures are generated and then awaited by the parent Dagster process.

Data is passed between step executions via [IO Managers](/guides/build/io-managers/). As a consequence, a persistent shared storage (such as a network filesystem shared by all of the Dask nodes, S3, or GCS) must be used.

Note that, when using this executor, the compute function of a single op is still executed in a single process on a single machine. If your goal is to distribute execution of workloads _within_ the logic of a single op, you may find that invoking Dask or PySpark directly from within the body of an op's compute function is a better fit than the engine layer covered in this documentation.

## Requirements

Install [dask.distributed](https://distributed.readthedocs.io/en/latest/install.html).

## Local execution

It is relatively straightforward to set up and run a Dagster job on local Dask. This can be useful for testing.

First, run `pip install dagster-dask`.

Then, create a job with the dask executor:

<CodeExample
  path="docs_snippets/docs_snippets/deploying/dask_hello_world.py"
  startAfter="start_local_job_marker"
  endBefore="end_local_job_marker"
/>

Now you can run this job with a config block such as the following:

<CodeExample path="docs_snippets/docs_snippets/deploying/dask_hello_world.yaml" />

Executing this job will spin up local Dask execution, run the job, and exit.

## Distributed execution

If you want to use a Dask cluster for distributed execution, you will first need to [set up a Dask cluster](https://distributed.readthedocs.io/en/latest/quickstart.html#setup-dask-distributed-the-hard-way). Note that the machine running the Dagster parent process must be able to connect to the host/port on which the Dask scheduler is running.

You'll also need an IO manager that uses persistent shared storage, which should be attached to the job along with any resources on which it depends. Here, we use the <PyObject section="libraries" module="dagster_aws" object="s3.s3_pickle_io_manager"/>:

<CodeExample
  path="docs_snippets/docs_snippets/deploying/dask_hello_world_distributed.py"
  startAfter="start_distributed_job_marker"
  endBefore="end_distributed_job_marker"
/>

For distributing task execution on a Dask cluster, you must provide a config block that includes the address/port of the Dask scheduler:

<CodeExample path="docs_snippets/docs_snippets/deploying/dask_remote.yaml" />

Since Dask will invoke your job code on the cluster workers, you must ensure that the latest version of your Python code is available to all of the Dask workers. Ideally, you'll package this as a Python module, and target your `workspace.yaml` at this module.

## Managing compute resources with Dask

Dask has [basic support](https://distributed.dask.org/en/latest/resources.html) for compute resource management. In Dask you can specify that a particular worker node has, say, 3 GPUs, and then tasks which are specified with GPU requirements will be scheduled to respect that constraint on available resources.

In Dask, you'd set this up by launching your workers with resource specifications:

```shell
dask-worker scheduler:8786 --resources "GPU=2"
```

and then when submitting tasks to the Dask cluster, specifying resource requirements in the Python API:

```python
client.submit(task, resources={'GPU': 1})
```

Dagster has simple support for Dask resource specification at the op level for ops that will be executed on Dask clusters. In your op definition, just add _tags_ as follows:

```python
@op(
    ...
    tags={'dagster-dask/resource_requirements': {"GPU": 1}},
)
def my_op(...):
    pass
```

The dict passed to `dagster-dask/resource_requirements` will be passed through as the `resources` argument to the Dask client's **`~dask:distributed.Client.submit`** method for execution on a Dask cluster. Note that in non-Dask execution, this key will be ignored.

## Caveats

Dagster logs are not yet retrieved from Dask workers; this will be addressed in follow-up work.

While this library is still nascent, we're working to improve it, and we are happy to accept contributions.
