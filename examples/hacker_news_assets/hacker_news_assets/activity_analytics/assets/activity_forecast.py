from pandas import DataFrame

from dagster import AssetIn, asset


@asset(ins={"activity_daily_stats": AssetIn(key_prefix="activity_analytics")})
def activity_forecast(activity_daily_stats: DataFrame) -> DataFrame:
    return activity_daily_stats.head(100)
