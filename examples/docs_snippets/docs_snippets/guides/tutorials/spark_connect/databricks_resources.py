import os

from databricks.connect import DatabricksSession

import dagster as dg

databricks_session = (
    DatabricksSession.builder.remote(
        host=os.environ["DATABRICKS_HOST"],
        token=os.environ["DATABRICKS_TOKEN"],
    )
    .serverless()
    .getOrCreate()
)


@dg.definitions
def resources():
    return dg.Definitions(resources={"spark": databricks_session})
