from typing import Any, Tuple

import numpy as np
import pandas as pd
from dagster_airbyte import airbyte_resource, build_airbyte_assets
from dagster_dbt import dbt_cli_resource, load_assets_from_dbt_project
from scipy import optimize

from dagster import AssetGroup, asset

from .constants import *  # pylint: disable=wildcard-import,unused-wildcard-import
from .pandas_io_manager import pandas_io_manager

airbyte_assets = build_airbyte_assets(
    connection_id=AIRBYTE_CONNECTION_ID, destination_tables=["orders", "users"]
)

dbt_assets = load_assets_from_dbt_project(
    project_dir=DBT_PROJECT_DIR, io_manager_key="pandas_io_manager"
)


@asset(compute_kind="python")
def order_forecast_model(daily_order_summary: pd.DataFrame) -> Any:
    """Model parameters that best fit the observed data"""
    df = daily_order_summary
    return tuple(
        optimize.curve_fit(
            f=model_func, xdata=df.order_date.astype(np.int64), ydata=df.num_orders, p0=[10, 100]
        )[0]
    )


@asset(compute_kind="python", io_manager_key="pandas_io_manager")
def predicted_orders(
    daily_order_summary: pd.DataFrame, order_forecast_model: Tuple[float, float]
) -> pd.DataFrame:
    """Predicted orders for the next 30 days based on the fit paramters"""
    a, b = order_forecast_model
    start_date = daily_order_summary.order_date.max()
    future_dates = pd.date_range(start=start_date, end=start_date + pd.DateOffset(days=30))
    predicted_data = model_func(x=future_dates.astype(np.int64), a=a, b=b)
    return pd.DataFrame({"order_date": future_dates, "num_orders": predicted_data})


analytics_assets = AssetGroup(
    airbyte_assets + dbt_assets + [order_forecast_model, predicted_orders],
    resource_defs={
        "airbyte": airbyte_resource.configured(AIRBYTE_CONFIG),
        "dbt": dbt_cli_resource.configured(DBT_CONFIG),
        "pandas_io_manager": pandas_io_manager.configured(PANDAS_IO_CONFIG),
    },
).build_job("Assets")
