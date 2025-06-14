import pandas as pd

import dagster as dg

from .assets import orders


# highlight-start
# Check that targets `orders`; block materialization of `augmented_orders` on failure
@dg.asset_check(asset=orders, blocking=True)
# highlight-end
def orders_id_has_no_nulls():
    orders_df = pd.read_csv("orders.csv")
    num_null_order_ids = orders_df["order_id"].isna().sum()
    return dg.AssetCheckResult(
        passed=bool(num_null_order_ids == 0),
    )
