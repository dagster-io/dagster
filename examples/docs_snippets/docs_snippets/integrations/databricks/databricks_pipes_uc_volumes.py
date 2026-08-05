import os

from dagster_databricks.pipes import PipesDatabricksServerlessClient
from databricks.sdk import WorkspaceClient
from databricks.sdk.service import jobs

import dagster as dg


@dg.asset
def feature_engineering(
    context: dg.AssetExecutionContext,
    pipes_databricks: PipesDatabricksServerlessClient,
) -> dg.MaterializeResult:
    task = jobs.SubmitTask.from_dict(
        {
            "task_key": "feature_engineering",
            "notebook_task": {
                "notebook_path": "/path/to/my/feature_engineering_notebook",
                "source": jobs.Source.WORKSPACE,
            },
        }
    )

    return pipes_databricks.run(
        task=task,
        context=context,
    ).get_materialize_result()


@dg.definitions
def resources():
    pipes_databricks_resource = PipesDatabricksServerlessClient(
        client=WorkspaceClient(
            host=os.environ["DATABRICKS_HOST"],
            token=os.environ["DATABRICKS_TOKEN"],
        ),
        # A Unity Catalog Volume used as the Pipes message transport
        volume_path="/Volumes/catalog/schema/dagster_pipes",
    )
    return dg.Definitions(
        assets=[feature_engineering],
        resources={"pipes_databricks": pipes_databricks_resource},
    )
