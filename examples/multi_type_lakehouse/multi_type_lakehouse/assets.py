import pandas as pd
from dagster.core.asset_defs import ForeignAsset, asset
from pandas import DataFrame as PandasDF
from pyspark.sql import DataFrame as SparkDF
from pyspark.sql import Window
from pyspark.sql import functions as f

sfo_q2_weather_sample = ForeignAsset("sfo_q2_weather_sample")


@asset
def daily_temperature_highs(sfo_q2_weather_sample: PandasDF) -> PandasDF:
    """Computes the temperature high for each day"""
    sfo_q2_weather_sample["valid_date"] = pd.to_datetime(sfo_q2_weather_sample["valid"])
    return sfo_q2_weather_sample.groupby("valid_date").max().rename(columns={"tmpf": "max_tmpf"})


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
