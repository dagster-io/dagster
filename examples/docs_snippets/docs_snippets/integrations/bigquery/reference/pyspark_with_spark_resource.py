from dagster_gcp_pyspark import BigQueryPySparkIOManager
from dagster_pyspark import pyspark_resource
from pyspark import SparkFiles
from pyspark.sql import (
    DataFrame,
    SparkSession,
)
from pyspark.sql.types import (
    DoubleType,
    StringType,
    StructField,
    StructType,
)

from dagster import AssetExecutionContext, Definitions, asset

BIGQUERY_JARS = "com.google.cloud.spark:spark-bigquery-with-dependencies_2.12:0.28.0"


@asset(required_resource_keys={"pyspark"})
def iris_data(context: AssetExecutionContext) -> DataFrame:
    spark = context.resources.pyspark.spark_session

    schema = StructType(
        [
            StructField("sepal_length_cm", DoubleType()),
            StructField("sepal_width_cm", DoubleType()),
            StructField("petal_length_cm", DoubleType()),
            StructField("petal_width_cm", DoubleType()),
            StructField("species", StringType()),
        ]
    )

    url = "https://docs.dagster.io/assets/iris.csv"
    spark.sparkContext.addFile(url)

    return spark.read.schema(schema).csv("file://" + SparkFiles.get("iris.csv"))


defs = Definitions(
    assets=[iris_data],
    resources={
        "io_manager": BigQueryPySparkIOManager(
            project="my-gcp-project",
            location="us-east5",
        ),
        "pyspark": pyspark_resource.configured(
            {"spark_conf": {"spark.jars.packages": BIGQUERY_JARS}}
        ),
    },
)
