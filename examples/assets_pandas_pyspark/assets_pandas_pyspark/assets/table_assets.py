# start_marker
import pandas as pd
from dagster import AssetKey, AssetSpec, Definitions, asset
from pandas import DataFrame

sfo_q2_weather_sample = AssetSpec(
    key=AssetKey("sfo_q2_weather_sample"),
    description="Weather samples, taken every five minutes at SFO",
    metadata={"format": "csv"},
)


@asset
def daily_temperature_highs(sfo_q2_weather_sample: DataFrame) -> DataFrame:
    """Computes the temperature high for each day."""
    sfo_q2_weather_sample["valid_date"] = pd.to_datetime(sfo_q2_weather_sample["valid"])
    return sfo_q2_weather_sample.groupby("valid_date").max().rename(columns={"tmpf": "max_tmpf"})


@asset
def hottest_dates(daily_temperature_highs: DataFrame) -> DataFrame:
    """Computes the 10 hottest dates."""
    return daily_temperature_highs.nlargest(10, "max_tmpf")


defs = Definitions(assets=[sfo_q2_weather_sample, daily_temperature_highs, hottest_dates])

# end_marker
