import os

from dagster_databricks.pipes import PipesDatabricksServerlessClient
from databricks.sdk import WorkspaceClient

import dagster as dg


@dg.asset
def feature_engineering(
    context: dg.AssetExecutionContext,
    pipes_databricks: PipesDatabricksServerlessClient,
) -> dg.MaterializeResult:
    return pipes_databricks.run_job(
        context=context,
        job_id=int(os.environ["DATABRICKS_JOB_ID"]),
        # Optional: job parameters for this run, alongside the Pipes params
        job_parameters={"target_schema": "analytics"},
        extras={"some_parameter": 42},
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
