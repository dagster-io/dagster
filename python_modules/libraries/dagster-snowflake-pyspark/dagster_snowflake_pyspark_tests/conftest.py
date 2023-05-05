import pytest
from pyspark.sql import SparkSession

SNOWFLAKE_JARS = (
    "net.snowflake:snowflake-jdbc:3.8.0,net.snowflake:spark-snowflake_2.12:2.8.2-spark_3.0"
)


@pytest.fixture(scope="module")
def spark():
    spark = SparkSession.builder.config(
        key="spark.jars.packages",
        value=SNOWFLAKE_JARS,
    ).getOrCreate()

    return spark
