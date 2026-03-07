import os

from databricks.connect import DatabricksSession
from pyspark.sql import SparkSession

import dagster as dg

# Create the Databricks session resource
databricks_session = (
    DatabricksSession.builder.remote(
        host=dg.EnvVar("DATABRICKS_HOST"),
        token=dg.EnvVar("DATABRICKS_TOKEN"),
    )
    .serverless()
    .getOrCreate()
)


@dg.definitions
def resources():
    return dg.Definitions(resources={"spark": databricks_session})


@dg.asset
def my_spark_asset(
    context: dg.AssetExecutionContext, spark: dg.ResourceParam[SparkSession]
):
    # This code runs in Dagster, but Spark operations execute on Databricks
    df = spark.sql("SELECT * FROM catalog.schema.table")
    result = df.filter(df.status == "active").count()
    return dg.MaterializeResult(metadata={"row_count": result})
