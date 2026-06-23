from datetime import date

from pyspark.sql import SparkSession
from pyspark.sql.types import DateType, IntegerType, StringType, StructField, StructType

import dagster as dg


@dg.asset
def airport_temps(
    context: dg.AssetExecutionContext, spark: dg.ResourceParam[SparkSession]
):
    """High and low temperature data by airport code and date."""
    schema = StructType(
        [
            StructField("AirportCode", StringType(), False),
            StructField("Date", DateType(), False),
            StructField("TempHighF", IntegerType(), False),
            StructField("TempLowF", IntegerType(), False),
        ]
    )

    data = [
        ["BLI", date(2021, 4, 3), 52, 43],
        ["BLI", date(2021, 4, 2), 50, 38],
        ["BLI", date(2021, 4, 1), 52, 41],
        ["PDX", date(2021, 4, 3), 64, 45],
        ["PDX", date(2021, 4, 2), 61, 41],
        ["PDX", date(2021, 4, 1), 66, 39],
        ["SEA", date(2021, 4, 3), 57, 43],
        ["SEA", date(2021, 4, 2), 54, 39],
        ["SEA", date(2021, 4, 1), 56, 41],
    ]

    temps = spark.createDataFrame(data, schema)

    spark.sql("USE default")
    spark.sql("DROP TABLE IF EXISTS airport_temps")
    temps.write.saveAsTable("airport_temps")

    temps.show()


@dg.asset(deps=[airport_temps])
def max_temps_by_code(
    context: dg.AssetExecutionContext, spark: dg.ResourceParam[SparkSession]
):
    """Max temperatures by airport code."""
    max_temps_by_code = spark.sql(
        "SELECT AirportCode, MAX(TempHighF) AS MaxTemp "
        "FROM airport_temps "
        "GROUP BY AirportCode"
    )
    spark.sql("DROP TABLE IF EXISTS max_temps_by_code")
    max_temps_by_code.write.saveAsTable("max_temps_by_code")

    max_temps_by_code.show()
