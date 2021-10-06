from dagster.core.asset_defs import asset
from pandas import DataFrame


@asset
def activity_forecast(activity_daily_stats: DataFrame) -> DataFrame:
    return activity_daily_stats.head(100)
