from typing import Tuple

import numpy as np
import pandas as pd
from dagster import AssetOut, multi_asset
from dagster_dbt.cli import DbtManifest

from assets_dbt_python.constants import MANIFEST_PATH
from assets_dbt_python.utils import random_data

manifest = DbtManifest.read(path=MANIFEST_PATH)


@multi_asset(
    outs={
        name: AssetOut(key=asset_key)
        for name, asset_key in manifest.get_asset_keys_by_output_name_for_source("raw_data").items()
    },
    compute_kind="random",
)
def randomly_generated_users_and_orders() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Randomly generates two tables:
    - users: a table containing all users data
    - orders: a table containing all orders that have been placed.
    """
    user_data = pd.DataFrame(
        {
            "user_id": range(1000),
            "company": np.random.choice(
                ["FoodCo", "ShopMart", "SportTime", "FamilyLtd"], size=1000
            ),
            "is_test_user": np.random.choice([True, False], p=[0.002, 0.998], size=1000),
        }
    )
    order_data = random_data(
        extra_columns={"order_id": str, "quantity": int, "purchase_price": float, "sku": str},
        n=10000,
    )
    return user_data, order_data
