from dagster_duckdb_pyspark import DuckDBPySparkIOManager
from dagster_pyspark import pyspark_resource
from pyspark import SparkFiles
from pyspark.sql import (
    DataFrame,
)
from pyspark.sql.types import (
    DoubleType,
    StringType,
    StructField,
    StructType,
)

from dagster import Definitions, asset


@asset(required_resource_keys={"pyspark"})
def iris_dataset(context) -> DataFrame:
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
    assets=[iris_dataset],
    resources={
        "io_manager": DuckDBPySparkIOManager(
            database="path/to/my_duckdb_database.duckdb",
            schema="IRIS",
        ),
        "pyspark": pyspark_resource,
    },
)
