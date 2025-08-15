import os

from dagster_databricks.pipes import PipesDatabricksServerlessClient
from databricks.sdk import WorkspaceClient
from databricks.sdk.service import jobs

import dagster as dg

pipes_databricks_resource = PipesDatabricksServerlessClient(
    client=WorkspaceClient(
        host=os.environ["DATABRICKS_HOST"],
        token=os.environ["DATABRICKS_TOKEN"],
    ),
    # A volume used to read and write for the pipes process
    volume_path="/Volumes/catalog/schema/volume",
)


@dg.asset
def databricks_asset(
    context: dg.AssetExecutionContext, pipes_databricks: PipesDatabricksServerlessClient
):
    task = jobs.SubmitTask.from_dict(
        {
            "task_key": "serverless_pipes_task",
            "notebook_task": {
                "notebook_path": "/path/to/my/notebook",
                "source": jobs.Source.WORKSPACE,
            },
        }
    )

    extras = {"some_parameter": 100}

    return pipes_databricks.run(
        task=task,
        context=context,
        extras=extras,
    ).get_materialize_result()


@dg.definitions
def resources():
    return dg.Definitions(
        assets=[databricks_asset],
        resources={"pipes_databricks": pipes_databricks_resource},
    )
