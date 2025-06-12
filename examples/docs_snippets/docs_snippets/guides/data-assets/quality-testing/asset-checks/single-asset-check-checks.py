import pandas as pd

import dagster as dg

from .assets import orders


# highlight-start
@dg.asset_check(asset=orders)
def orders_id_has_no_nulls():
    orders_df = pd.read_csv("orders.csv")
    num_null_order_ids = orders_df["order_id"].isna().sum()

    # Return the result of the check
    return dg.AssetCheckResult(
        # Define passing criteria
        passed=bool(num_null_order_ids == 0),
    )
    # highlight-end
