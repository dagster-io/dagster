# pylint: disable=redefined-outer-name

# start_marker
import pandas as pd
from dagster import AssetKey
from dagster.core.asset_defs import ForeignAsset, asset
from pandas import DataFrame

sfo_q2_weather_sample = ForeignAsset(key=AssetKey("sfo_q2_weather_sample"))


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
