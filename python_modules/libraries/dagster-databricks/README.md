# dagster-databricks

The docs for `dagster-databricks` can be found
[here](https://docs.dagster.io/_apidocs/libraries/dagster-databricks).

## Pipes example

This package includes a prototype API for launching Databricks jobs with
Dagster's Pipes protocol. There are two ways to use the API:

### (1) `PipesDatabricksClient` resource

The `PipesDatabricksClient` resource provides a high-level API for launching
Databricks jobs using Dagster's Pipes protocol.

`PipesDatabricksClient.run` takes a single
`databricks.sdk.service.jobs.SubmitTask` specification. After setting up Pipes
communications channels (which by default use DBFS), it injects the information
needed to connect to these channels from Databricks into the task
specification. It then launches a Databricks job by passing the specification
to `WorkspaceClient.jobs.submit`. It synchronously executes the job and returns
a `PipesClientCompletedInvocation` object that exposes a `get_results` method.
The output of `get_results` is a tuple of `PipesExecutionResult` objects that
you can return from the asset compute function.


```
import os
from dagster import AssetExecutionContext, Definitions, asset
from dagster_databricks import PipesDatabricksClient
from databricks.sdk import WorkspaceClient
from databricks.sdk.service import jobs

@asset
def databricks_asset(context: AssetExecutionContext, pipes_client: PipesDatabricksClient):

    # task specification will be passed to Databricks as-is, except for the
    # injection of environment variables
    task = jobs.SubmitTask.from_dict({
        "new_cluster": { ... },
        "libraries": [
            # must include dagster-pipes
            {"pypi": {"package": "dagster-pipes"}},
        ],
        "task_key": "some-key",
        "spark_python_task": {
            "python_file": "dbfs:/myscript.py",
            "source": jobs.Source.WORKSPACE,
        }
    })

    # Arbitrary json-serializable data you want access to from the `PipesSession`
    # in the Databricks runtime. Assume `sample_rate` is a parameter used by
    # the target job's business logic.
    extras = {"sample_rate": 1.0}

    # synchronously execute the databricks job
    return pipes_client.run(
        task=task,
        context=context,
        extras=extras,
    ).get_results()

client = WorkspaceClient(
    host=os.environ["DATABRICKS_HOST"],
    token=os.environ["DATABRICKS_TOKEN"],
)

defs = Definitions(
    assets=[databricks_asset],
    resources = {"pipes_client": PipesDatabricksClient(client)}
)
```

`PipesDatabricksClient.run` requires that the targeted python script
(`dbfs:/myscript.py` above) already exist in DBFS. Here is what it might look
like:

```
### dbfs:/myscript.py

# `dagster_pipes` must be available in the databricks python environment
from dagster_pipes import PipesDbfsContextLoader, PipesDbfsMessageWriter, init_dagster_pipes

# Sets up communication channels and downloads the context data sent from Dagster.
# Note that while other `context_loader` and `message_writer` settings are
# possible, it is recommended to use the below settings for Databricks.
context = init_dagster_pipes(
    context_loader=PipesDbfsContextLoader(),
    message_writer=PipesDbfsMessageWriter()
)

# Access the `extras` dict passed when launching the job from Dagster.
sample_rate = context.get_extra("sample_rate")

# Stream log message back to Dagster
context.log(f"Using sample rate: {sample_rate}")

# ... your code that computes and persists the asset

# Stream asset materialization metadata and data version back to Dagster.
# This should be called after you've computed and stored the asset value. We
# omit the asset key here because there is only one asset in scope, but for
# multi-assets you can pass an `asset_key` parameter.
context.report_asset_materialization(
    metadata={"some_metric", {"raw_value": get_metric(), "type": "text"}},
    data_version = get_data_version()
)
```

### (2) `open_pipes_session` context manager

If you have existing code to launch/poll the job you do not want to change, you
want to stream back results, or you just want more control than is permitted by
`PipesDatabricksClient`, you can use `open_pipes_session`. All that is
necessary is that (1) your Databricks job be launched within the scope of the
`open_pipes_session` context manager; (2) your job is launched on a cluster
containing the environment variables available on the yielded `pipes_session`. 

While your Databricks code is running, any calls to
`report_asset_materialization` in the external script are streamed back to
Dagster, causing a `MaterializationResult` object to be buffered on the
`pipes_session`. You can either leave these objects buffered until execution is
complete (Option (1) in below example code) or stream them to Dagster machinery
during execution by calling `yield pipes_session.get_results()` (Option (2)).

With either option, once the `open_pipes_session` block closes, you must call
`yield pipes_session.get_results()` to yield any remaining buffered results,
since we cannot guarantee that all communications from Databricks have been
processed until the `open_pipes_session` block closes.

```
import os

from dagster import AssetExecutionContext, ext_protocol
from dagster_databricks import PipesDbfsContextInjector, PipesDbfsMessageReader
from databricks.sdk import WorkspaceClient

@asset
def databricks_asset(context: AssetExecutionContext):
    
    client = WorkspaceClient(
        host=os.environ["DATABRICKS_HOST"],
        token=os.environ["DATABRICKS_TOKEN"],
    )

    # Arbitrary json-serializable data you want access to from the `PipesContext`
    # in the Databricks runtime. Assume `sample_rate` is a parameter used by
    # the target job's business logic.
    extras = {"sample_rate": 1.0}

    # Sets up Pipes communications channels
    with open_pipes_session(
        context=context,
        extras=extras,
        context_injector=PipesDbfsContextInjector(client=client),
        message_reader=PipesDbfsMessageReader(client=client),
    ) as pipes_session:
        
        ##### Option (1)
        # NON-STREAMING. Just pass the necessary environment variables down.
        # During execution, all reported materializations are buffered on the
        # `pipes_session`. Yield them all after Databricks execution is finished.

        # Dict[str, str] with environment variables containing Pipes comms info.
        env_vars = pipes_session.get_pipes_bootstrap_env_vars()

        # Some function that handles launching/monitoring of the Databricks job.
        # It must ensure that the `env_vars` are set on the executing cluster.
        custom_databricks_launch_code(env_vars)

        ##### Option (2)
        # STREAMING. Pass `pipes_session` down. During execution, you can yield any
        # asset materializations that have been reported by calling `
        # pipes_session.get_results()` as often as you like. `get_results` returns
        # an iterator that your custom code can `yield from` to forward the
        # results back to the materialize function. Note you will need to extract
        # the env vars by calling `pipes_session.get_pipes_bootstrap_env_vars()`,
        # and launch the Databricks job in the same way as with (1).

        # The function should return an `Iterator[MaterializeResult]`.
        yield from custom_databricks_launch_code(pipes_session)

    # With either option (1) or (2), this is required to yield any remaining
    # buffered results.
    yield from pipes_session.get_results()
```
