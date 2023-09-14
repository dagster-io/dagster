# dagster-databricks

The docs for `dagster-databricks` can be found
[here](https://docs.dagster.io/_apidocs/libraries/dagster-databricks).

## ext example

This package includes a prototype API for launching databricks jobs with
Dagster's EXT protocol. There are two ways to use the API:

### (1) `ExtDatabricks` resource

The `ExtDatabricks` resource provides a high-level API for launching
databricks jobs using Dagster's ext protocol.

`ExtDatabricks.run` takes a single `databricks.sdk.service.jobs.SubmitTask`
specification. After setting up ext communications channels (which by default
use DBFS), it injects the information needed to connect to these channels from
Databricks into the task specification. It then launches a Databricks job by
passing the specification to `WorkspaceClient.jobs.submit`. It polls the job
state and exits gracefully on success or failure:


```
import os
from dagster import AssetExecutionContext, Definitions, asset
from dagster_databricks import ExtDatabricks
from databricks.sdk import WorkspaceClient
from databricks.sdk.service import jobs

@asset
def databricks_asset(context: AssetExecutionContext, ext: ExtDatabricks):

    # task specification will be passed to databricks as-is, except for the
    # injection of environment variables
    task = jobs.SubmitTask.from_dict({
        "new_cluster": { ... },
        "libraries": [
            # must include dagster-ext-process
            {"pypi": {"package": "dagster-ext-process"}},
        ],
        "task_key": "some-key",
        "spark_python_task": {
            "python_file": "dbfs:/myscript.py",
            "source": jobs.Source.WORKSPACE,
        }
    })

    # Arbitrary json-serializable data you want access to from the `ExtContext`
    # in the databricks runtime. Assume `sample_rate` is a parameter used by
    # the target job's business logic.
    extras = {"sample_rate": 1.0}

    # synchronously execute the databricks job
    ext.run(
        task=task,
        context=context,
        extras=extras,
    )

client = WorkspaceClient(
    host=os.environ["DATABRICKS_HOST"],
    token=os.environ["DATABRICKS_TOKEN"],
)

defs = Definitions(
    assets=[databricks_asset],
    resources = {"ext": ExtDatabricks(client)}
)
```

`ExtDatabricks.run` requires that the targeted python script
(`dbfs:/myscript.py` above) already exist in DBFS. Here is what it might look
like:

```
### dbfs:/myscript.py

# `dagster_ext` must be available in the databricks python environment
from dagster_ext import ExtDbfsContextLoader, ExtDbfsMessageWriter, init_dagster_ext

# Sets up communication channels and downloads the context data sent from Dagster.
# Note that while other `context_loader` and `message_writer` settings are
# possible, it is recommended to use the below settings for Databricks.
context = init_dagster_ext(
    context_loader=ExtDbfsContextLoader(),
    message_writer=ExtDbfsMessageWriter()
)

# Access the `extras` dict passed when launching the job from Dagster.
sample_rate = context.get_extra("sample_rate")

# Stream log message back to Dagster
context.log(f"Using sample rate: {sample_rate}")

# ... your code that computes and persists the asset

# Stream arbitrary metadata back to Dagster. This will be attached to the
# associated `AssetMaterialization`
context.report_asset_metadata("some_metric", get_metric(), metadata_type="text")

# Stream data version back to Dagster. This will also be attached to the
# associated `AssetMaterialization`.
context.report_asset_data_version(get_data_version())
```

### (2) `ext_protocol` context manager

If you have existing code to launch/poll the job you do not want to change, or
you just want more control than is permitted by `ExtDatabricks`, you can use
`ext_protocol`. All that is necessary is that (1) your Databricks job be
launched within the scope of the `ext_process` context manager; (2) your job is
launched on a cluster containing the environment variables available on the
yielded `ext_context`. 

```
import os

from dagster import AssetExecutionContext, ext_protocol
from dagster_databricks import ExtDbfsContextInjector, ExtDbfsMessageReader
from databricks.sdk import WorkspaceClient

@asset
def databricks_asset(context: AssetExecutionContext):
    
    client = WorkspaceClient(
        host=os.environ["DATABRICKS_HOST"],
        token=os.environ["DATABRICKS_TOKEN"],
    )

    # Arbitrary json-serializable data you want access to from the `ExtContext`
    # in the databricks runtime. Assume `sample_rate` is a parameter used by
    # the target job's business logic.
    extras = {"sample_rate": 1.0}

    # Sets up ext communications channels
    with ext_protocol(
        context=context,
        extras=extras,
        context_injector=ExtDbfsContextInjector(client=client),
        message_reader=ExtDbfsMessageReader(client=client),
    ) as ext_context:
        
        # Dict[str, str] with environment variables containing ext comms info.
        env_vars = ext_context.get_external_process_env_vars()

        # Some function that handles launching/monitoring of the databricks job.
        # It must ensure that the `env_vars` are set on the executing cluster.
        custom_databricks_launch_code(env_vars)
```
