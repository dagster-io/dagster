# Dask Deployment Guide

## Introduction
As noted above, Dagster is designed to target a variety of execution substrates, and natively supports Dask for pipeline execution.

Presently, the Dagster / Dask integration provides a single API, `execute_on_dask`, which can execute a Dagster pipeline on either local Dask or on a remote Dask cluster.

This is accomplished by taking the compiled execution plan, and converting each execution step into a [Dask Future](https://docs.dask.org/en/latest/futures.html) configured with the appropriate task dependencies to ensure tasks are properly sequenced. Data is passed between step executions via intermediate storage, and so a persistent shared storage must be used in a distributed execution context. When the pipeline is executed, these futures are generated and then awaited by the parent Dagster process.


### Requirements
To use `dagster-dask`, you'll need to install [Dask / Dask.Distributed](https://distributed.readthedocs.io/en/latest/install.html).

## Local Execution
It is relatively straightforward to set up and run a Dagster pipeline on Dask, using the `execute_on_dask()` API. First,

`pip install dagster dagster-dask`

Then:

```
# dask_hello_world.py

python
from dagster import pipeline, solid, ExecutionTargetHandle
from dagster_dask import execute_on_dask, DaskConfig


@solid
def hello_world(_):
    return "Hello, World!"


@pipeline
def dask_pipeline():
    return hello_world()  # pylint: disable=no-value-for-parameter


execute_on_dask(
    ExecutionTargetHandle.for_pipeline_python_file(__file__, 'dask_pipeline'),
    env_config={'storage': {'filesystem': {}}},
)
```

Running `python dask_hello_world.py` will spin up local Dask execution, run the hello, world Dagster pipeline, and exit.


## Distributed Cluster Execution
If you want to use a Dask cluster for distributed execution, you will first need to [set up a Dask cluster](https://distributed.readthedocs.io/en/latest/quickstart.html#setup-dask-distributed-the-hard-way). Note that the machine running the Dagster parent process must have access to the host/port on which the Dask scheduler is running.

For distributing task execution on a Dask cluster, you must provide a `DaskConfig` object with the address/port of the Dask scheduler:

```
execute_on_dask(
    ExecutionTargetHandle.for_pipeline_module('your.python.module', 'your_pipeline_name'),
    env_config={'storage': {'s3': {'config': {'s3_bucket': 'YOUR_BUCKET_HERE'}}}},
    dask_config=DaskConfig(address='dask_scheduler.dns-name:8787')
)
```

Since Dask will invoke your pipeline code on the cluster workers, you must ensure that the latest version of your Python code is available to all of the Dask workers—ideally packaged as a Python module `your.python.module` that is importable on `PYTHONPATH`.


## Limitations
* Presently, `dagster-dask` does not support launching Dask workloads from Dagit.
* For distributed execution, you must use S3 for intermediates and run storage, as shown above.
* Dagster logs are not yet retrieved from Dask workers; this will be addressed in follow-up work.

While this library is still nascent, we're working to improve it, and we are happy to accept contributions!
