import os

from pyspark.sql import SparkSession

import dagster as dg

spark_session = SparkSession.builder.remote(
    os.environ["SPARK_REMOTE"],
).getOrCreate()


@dg.definitions
def resources():
    return dg.Definitions(resources={"spark": spark_session})
