import numpy as np
from pandas import DataFrame, DateOffset, date_range

from dagster import asset


@asset(compute_kind="python", io_manager_key="warehouse_io_manager")
def activity_forecast(activity_daily_stats: DataFrame) -> DataFrame:
    """Forecast of activity for the next 30 days"""
    start_date = activity_daily_stats.date.max()
    future_dates = date_range(start=start_date, end=start_date + DateOffset(days=30))
    predicted_data = 0.5 * np.exp(7 * (future_dates.astype(np.int64) / 10**18 - 1.6095))
    return DataFrame({"date": future_dates, "num_comments": predicted_data})
