# dagster-dask

## Introduction
This library provides an integration with Dask / Dask.Distributed, to support distributed execution of Dagster workloads. It is still early, and has some limitations which are discussed below.

Presently, it provides a single API, `execute_on_dask`, which can execute a Dagster pipeline on either local Dask or a remote Dask cluster.

## Requirements
To use `dagster-dask`, you'll need to [install Dask / Dask.Distributed](https://distributed.readthedocs.io/en/latest/install.html).

If you want to use a cluster for distributed execution, you'll need to [set up a Dask cluster](https://distributed.readthedocs.io/en/latest/quickstart.html#setup-dask-distributed-the-hard-way). Note that you'll need to ensure that Dagster can access the host/port on which the Dask scheduler is running.

## Getting Started
There is a simple example of how to use this library in [the tests folder](https://github.com/dagster-io/dagster/tree/master/python_modules/dagster-dask/dagster_dask_tests/test_execute.py). This example showcases how to set up a "hello, world" with local Dask execution.

For distributed execution on a Dask cluster, you'll just need to provide a `DaskConfig` object with the address/port of the Dask scheduler:

```
execute_on_dask(
    ExecutionTargetHandle.for_pipeline_fn(define_pipeline),
    env_config={'storage': {'s3': {}}},
    dask_config=DaskConfig(address='dask_scheduler.dns-name:8787')
)
```


## Limitations
* Presently, `dagster-dask` does not support launching Dask workloads from Dagit.
* For distributed execution, you must use S3 for intermediates and run storage, as shown above.
* Dagster logs are not yet retrieved from Dask workers; this will be addressed in follow-up work.

While this library is still nascent, we're working to improve it, and we are happy to accept contributions!
