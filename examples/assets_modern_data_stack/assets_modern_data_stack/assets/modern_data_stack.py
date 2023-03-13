import numpy as np
import pandas as pd
from assets_modern_data_stack.assets.airbyte_iaac import (
    airbyte_instance,
    postgres_to_postgres,
)
from dagster import asset
from dagster._utils import file_relative_path
from dagster_airbyte import load_assets_from_connections
from dagster_dbt import load_assets_from_dbt_project
from scipy import optimize

DBT_PROJECT_DIR = file_relative_path(__file__, "../../dbt_project")
DBT_PROFILES_DIR = file_relative_path(__file__, "../../dbt_project/config")
DBT_CONFIG = {"project_dir": DBT_PROJECT_DIR, "profiles_dir": DBT_PROFILES_DIR}


airbyte_assets = load_assets_from_connections(
    airbyte=airbyte_instance,
    connections=[postgres_to_postgres],
    key_prefix="postgres_replica",
)


dbt_assets = load_assets_from_dbt_project(
    project_dir=DBT_PROJECT_DIR, io_manager_key="db_io_manager"
)


def model_func(x, a, b):
    return a * np.exp(b * (x / 10**18 - 1.6095))


@asset(compute_kind="python")
def order_forecast_model(daily_order_summary: pd.DataFrame) -> np.ndarray:
    """Model parameters that best fit the observed data."""
    train_set = daily_order_summary
    return optimize.curve_fit(
        f=model_func,
        xdata=train_set.order_date.astype(np.int64),
        ydata=train_set.num_orders,
        p0=[10, 100],
    )[0]


@asset(compute_kind="python", io_manager_key="db_io_manager")
def predicted_orders(
    daily_order_summary: pd.DataFrame, order_forecast_model: np.ndarray
) -> pd.DataFrame:
    """Predicted orders for the next 30 days based on the fit paramters."""
    a, b = tuple(order_forecast_model)
    start_date = daily_order_summary.order_date.max()
    future_dates = pd.date_range(
        start=start_date, end=start_date + pd.DateOffset(days=30)
    )
    predicted_data = model_func(x=future_dates.astype(np.int64), a=a, b=b)
    return pd.DataFrame({"order_date": future_dates, "num_orders": predicted_data})
