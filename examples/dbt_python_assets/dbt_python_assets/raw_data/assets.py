import numpy as np
import pandas as pd

from dagster import asset

from ..utils import random_data


@asset
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


@asset
def orders() -> pd.DataFrame:
    import time

    time.sleep(2)
    """A table containing all orders that have been placed"""
    return random_data(
        extra_columns={"order_id": str, "quantity": int, "purchase_price": float, "sku": str},
        n=10000,
    )
