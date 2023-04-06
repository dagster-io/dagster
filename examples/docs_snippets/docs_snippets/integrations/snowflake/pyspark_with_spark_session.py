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
    spark = SparkSession.builder.config(
        key="spark.jars.packages",
        value=SNOWFLAKE_JARS,
    ).getOrCreate()

    schema = StructType(
        [
            StructField("Sepal length (cm)", DoubleType()),
            StructField("Sepal width (cm)", DoubleType()),
            StructField("Petal length (cm)", DoubleType()),
            StructField("Petal width (cm)", DoubleType()),
            StructField("Species", StringType()),
        ]
    )

    url = "https://archive.ics.uci.edu/ml/machine-learning-databases/iris/iris.data"
    spark.sparkContext.addFile(url)

    return spark.read.schema(schema).csv("file://" + SparkFiles.get("iris.data"))


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
