from dagster_snowflake_pyspark import SnowflakePySparkIOManager
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

from dagster import Definitions, EnvVar, asset

SNOWFLAKE_JARS = "net.snowflake:snowflake-jdbc:3.8.0,net.snowflake:spark-snowflake_2.12:2.8.2-spark_3.0"


@asset
def iris_dataset() -> DataFrame:
    spark = SparkSession.builder.config(  # type: ignore
        key="spark.jars.packages",
        value=SNOWFLAKE_JARS,
    ).getOrCreate()

    schema = StructType(
        [
            StructField("sepal_length_cm", DoubleType()),
            StructField("sepal_width_cm", DoubleType()),
            StructField("petal_length_cm", DoubleType()),
            StructField("petal_width_cm", DoubleType()),
            StructField("species", StringType()),
        ]
    )

    url = ("https://docs.dagster.io/assets/iris.csv",)
    spark.sparkContext.addFile(url)

    return spark.read.schema(schema).csv("file://" + SparkFiles.get("iris.csv"))


defs = Definitions(
    assets=[iris_dataset],
    resources={
        "io_manager": SnowflakePySparkIOManager(
            account="abc1234.us-east-1",
            user=EnvVar("SNOWFLAKE_USER"),
            password=EnvVar("SNOWFLAKE_PASSWORD"),
            database="FLOWERS",
            warehouse="PLANTS",
            schema="IRIS",
        ),
    },
)
