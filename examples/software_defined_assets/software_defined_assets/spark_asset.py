from pyspark.sql import DataFrame as SparkDF
from pyspark.sql import Window
from pyspark.sql import functions as f

from dagster import asset


@asset
def daily_temperature_high_diffs(daily_temperature_highs: SparkDF) -> SparkDF:
    """Computes the difference between each day's high and the previous day's high"""
    window = Window.orderBy("valid_date")
    return daily_temperature_highs.select(
        "valid_date",
        (
            daily_temperature_highs["max_tmpf"]
            - f.lag(daily_temperature_highs["max_tmpf"]).over(window)
        ).alias("day_high_diff"),
    )
