# pylint: disable=redefined-outer-name

# start_marker
import pandas as pd
from pandas import DataFrame

from dagster import AssetKey, SourceAsset, asset

sfo_q2_weather_sample = SourceAsset(
    key=AssetKey("sfo_q2_weather_sample"),
    description="Weather samples, taken every five minutes at SFO",
    metadata={"format": "csv"},
)


@asset
def daily_temperature_highs(sfo_q2_weather_sample: DataFrame) -> DataFrame:
    """Computes the temperature high for each day"""
    sfo_q2_weather_sample["valid_date"] = pd.to_datetime(sfo_q2_weather_sample["valid"])
    return sfo_q2_weather_sample.groupby("valid_date").max().rename(columns={"tmpf": "max_tmpf"})


@asset
def hottest_dates(daily_temperature_highs: DataFrame) -> DataFrame:
    """Computes the 10 hottest dates"""
    return daily_temperature_highs.nlargest(10, "max_tmpf")


# end_marker
