import os

from dagster_databricks import PipesDatabricksClient

import dagster as dg
from databricks.sdk import WorkspaceClient

pipes_databricks_resource = PipesDatabricksClient(
    client=WorkspaceClient(
        host=os.environ["DATABRICKS_HOST"],
        token=os.environ["DATABRICKS_TOKEN"],
    )
)


@dg.definitions
def resources():
    return dg.Definitions(resources={"pipes_databricks": pipes_databricks_resource})
