import numpy as np
import pandas as pd
from assets_dbt_python.utils import random_data

from dagster import asset


@asset(compute_kind="random")
def users() -> pd.DataFrame:
    """A table containing all users data"""
    return pd.DataFrame(
        {
            "user_id": range(1000),
            "company": np.random.choice(
                ["FoodCo", "ShopMart", "SportTime", "FamilyLtd"], size=1000
            ),
            "is_test_user": np.random.choice([True, False], p=[0.002, 0.998], size=1000),
        }
    )


@asset(compute_kind="random")
def orders() -> pd.DataFrame:
    """A table containing all orders that have been placed"""
    return random_data(
        extra_columns={"order_id": str, "quantity": int, "purchase_price": float, "sku": str},
        n=10000,
    )
