import numpy as np
import pandas as pd
from typing import Tuple, Any

from dagster import asset, AssetIn


def model_func(x, a, b):
    return a * np.exp(b * (x / 10**18 - 1.6095))


@asset(ins={"daily_order_summary": AssetIn(key_prefix=["duckdb", "dbt_schema"])})
def order_forecast_model(daily_order_summary: pd.DataFrame) -> Any:
    """Model parameters that best fit the observed data"""
    df = daily_order_summary
    return tuple(
        optimize.curve_fit(
            f=model_func, xdata=df.order_date.astype(np.int64), ydata=df.num_orders, p0=[10, 100]
        )[0]
    )


'''
@asset(
    ins={
        "daily_order_summary": AssetIn(key_prefix=["duckdb", "analytics"]),
        "order_forecast_model": AssetIn(),
    }
)
def predicted_orders(
    daily_order_summary: pd.DataFrame, order_forecast_model: Tuple[float, float]
) -> pd.DataFrame:
    """Predicted orders for the next 30 days based on the fit paramters"""
    a, b = order_forecast_model
    start_date = daily_order_summary.order_date.max()
    future_dates = pd.date_range(start=start_date, end=start_date + pd.DateOffset(days=30))
    predicted_data = model_func(x=future_dates.astype(np.int64), a=a, b=b)
    return pd.DataFrame({"order_date": future_dates, "num_orders": predicted_data})
'''
