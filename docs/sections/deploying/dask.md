# Deploying on Dask

## Introduction

As noted above, Dagster is designed to target a variety of execution substrates, and natively
supports Dask for pipeline execution.

The Dagster / Dask integration lets you execute a Dagster pipeline on either local Dask or on a
remote Dask cluster by specifying the `run_config` argument to `execute_pipeline`.

The integration works by taking the compiled execution plan, and converting each execution step
into a [Dask Future](https://docs.dask.org/en/latest/futures.html) configured with the appropriate
task dependencies to ensure tasks are properly sequenced. When the pipeline is executed, these
futures are generated and then awaited by the parent Dagster process.

Data is passed between step executions via intermediate storage. As a consequence, a persistent
shared storage must be used in a distributed execution context.

### Requirements

To use `dagster-dask`, you'll need to install
[Dask / Dask.Distributed](https://distributed.readthedocs.io/en/latest/install.html).

## Local Execution

It is relatively straightforward to set up and run a Dagster pipeline on Dask.

First, run `pip install dagster dagster-dask`.

Then:

```
# dask_hello_world.py

python
from dagster import execute_pipeline, ExecutionTargetHandle, ModeDefinition, pipeline, solid
from dagster.core.definitions.executor import default_executors
from dagster_dask import dask_executor


@solid
def hello_world(_):
    return "Hello, World!"


@pipeline(mode_defs=ModeDefinition(executor_defs=default_executors + [dask_executor]))
def dask_pipeline():
    return hello_world()  # pylint: disable=no-value-for-parameter


execute_pipeline(
    ExecutionTargetHandle.for_pipeline_python_file(__file__, 'dask_pipeline'),
    env_config={'storage': {'filesystem': {}}, 'execution': {'dask': {}}},
)
```

Running `python dask_hello_world.py` will spin up local Dask execution, run the Dagster pipeline,
and exit.

## Distributed Cluster Execution

If you want to use a Dask cluster for distributed execution, you will first need to
[set up a Dask cluster](https://distributed.readthedocs.io/en/latest/quickstart.html#setup-dask-distributed-the-hard-way).
Note that the machine running the Dagster parent process must have access to the host/port on which
the Dask scheduler is running.

For distributing task execution on a Dask cluster, you must provide a `DaskConfig` object with
the address/port of the Dask scheduler:

```
execute_pipeline(
    ExecutionTargetHandle.for_pipeline_module('your.python.module', 'your_pipeline_name'),
    env_config={
        'storage': {'s3': {'config': {'s3_bucket': 'YOUR_BUCKET_HERE'}}},
        'execution': {'dask': {'config': {'address': 'dask_scheduler.dns-name:8787'}}}
    },
)
```

Since Dask will invoke your pipeline code on the cluster workers, you must ensure that the latest
version of your Python code is available to all of the Dask workers—ideally packaged as a Python
module `your.python.module` that is importable on `PYTHONPATH`.

## Dask Resources

Dask has [basic support](https://distributed.dask.org/en/latest/resources.html) for resource
management. In Dask you can specify that a particular worker node has, say, 3 GPUs, and then tasks
which are specified with GPU requirements will be scheduled to respect that constraint on available
resources.

In Dask, you'd set this up by launching your workers with resource specifications:

```bash
dask-worker scheduler:8786 --resources "GPU=2"
```

and then when submitting tasks to the Dask cluster, specifying resource requirements:

```
client.submit(task, resources={'GPU': 1})
```

Dagster has simple support for Dask resource specification at the solid level for solids that will
be executed on Dask clusters. In your solid definition, just add a `step_metadata_fn` as follows:

```python
@solid(
    ...
    step_metadata_fn=lambda _: {'dagster-dask/resource_requirements': {'GPU': 1}},
)
def my_task(context):
    pass
```

And these requirements will be passed along to Dask when executed on a Dask cluster. Note that in
non-Dask contexts, this key will be ignored.

## Limitations

- For distributed execution, you must use S3 for intermediates and run storage, as shown above.
- Dagster logs are not yet retrieved from Dask workers; this will be addressed in follow-up work.

While this library is still nascent, we're working to improve it, and we are happy to accept
contributions!
