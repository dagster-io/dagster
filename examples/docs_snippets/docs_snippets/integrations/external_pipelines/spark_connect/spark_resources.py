import os

from pyspark.sql import SparkSession

import dagster as dg


@dg.definitions
def resources():
    spark_session = SparkSession.builder.remote(
        os.environ["SPARK_REMOTE"],
    ).getOrCreate()

    return dg.Definitions(resources={"spark": spark_session})
