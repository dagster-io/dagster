# pylint: disable=redefined-outer-name

# start_marker
import pandas as pd
from dagster import AssetKey, Out, Output
from dagster.core.asset_defs import ForeignAsset, asset, multi_asset
from pandas import DataFrame

sfo_q2_weather_sample = ForeignAsset(
    key=AssetKey("sfo_q2_weather_sample"),
    description="Weather samples, taken every five minutes at SFO",
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


"""
@multi_asset(outs={"a": Out(int), "b": Out(int), "c": Out(int)})
def foo(hottest_dates):
    yield Output(1, "a")
    yield Output(2, "b")
    yield Output(3, "c")
    """


@multi_asset(
    outs={
        "xyz": Out(DataFrame, asset_key=AssetKey(["xyz"])),
        "abc": Out(DataFrame, asset_key=AssetKey(["abc"]), in_deps=[]),
        "df": Out(DataFrame, asset_key=AssetKey(["df"]), out_deps=["xyz", "abc"]),
        "eg": Out(DataFrame, asset_key=AssetKey(["eg"]), out_deps=["df", "abc"]),
    }
)
def foo(hottest_dates: DataFrame):
    yield Output(hottest_dates, "xyz")
    yield Output(hottest_dates, "abc")
    yield Output(hottest_dates, "df")
    yield Output(hottest_dates, "eg")


# end_marker
