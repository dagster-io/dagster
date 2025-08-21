import os

from databricks.connect import DatabricksSession

import dagster as dg


@dg.definitions
def resources():
    databricks_session = (
        DatabricksSession.builder.remote(
            host=os.environ["DATABRICKS_HOST"],
            token=os.environ["DATABRICKS_TOKEN"],
        )
        .serverless()
        .getOrCreate()
    )

    return dg.Definitions(resources={"spark": databricks_session})
