import pandas as pd

import dagster as dg


@dg.asset
def orders():
    orders_df = pd.DataFrame({"order_id": [1, 2], "item_id": [432, 878]})
    orders_df.to_csv("orders.csv")


@dg.asset(deps=[orders])
def augmented_orders():
    orders_df = pd.read_csv("orders.csv")
    augmented_orders_df = orders_df.assign(description=["item_432", "item_878"])
    augmented_orders_df.to_csv("augmented_orders.csv")
