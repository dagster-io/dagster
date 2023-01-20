from dagster_snowflake_pyspark import snowflake_pyspark_io_manager
from pyspark.sql import DataFrame, DoubleType, SparkSession, StringType, StructType

from dagster import Definitions, asset

SNOWFLAKE_JARS = (
    "net.snowflake:snowflake-jdbc:3.8.0,net.snowflake:spark-snowflake_2.12:2.8.2-spark_3.0"
)


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

    return spark.read.schema(schema).csv(
        "https://archive.ics.uci.edu/ml/machine-learning-databases/iris/iris.data"
    )


defs = Definitions(
    assets=[iris_dataset],
    resources={
        "io_manager": snowflake_pyspark_io_manager.configured(
            {
                "account": "abc1234.us-east-1",
                "user": {"env": "SNOWFLAKE_USER"},
                "password": {"env": "SNOWFLAKE_PASSWORD"},
                "database": "FLOWERS",
                "warehouse": "PLANTS",
                "schema": "IRIS,",
            }
        )
    },
)
