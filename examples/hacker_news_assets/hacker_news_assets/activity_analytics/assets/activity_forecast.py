from pandas import DataFrame

from dagster import asset


@asset
def activity_forecast(activity_daily_stats: DataFrame) -> DataFrame:
    return activity_daily_stats.head(100)
