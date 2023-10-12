import pandas as pd
from dagster_pipes import PipesContext, open_dagster_pipes


def main():
    orders_df = pd.DataFrame(
        {"order_id": [1, 2, 3], "item_id": [432, 878, 102], "user_id": ["a", "b", "a"]}
    )
    total_orders = len(orders_df)
    total_users = orders_df["user_id"].nunique()

    # get the Dagster Pipes context
    pipes = PipesContext.get()
    # send structured metadata back to Dagster. asset_key is required when there are multiple assets
    pipes.report_asset_materialization(
        asset_key="orders", metadata={"total_orders": total_orders}
    )
    pipes.report_asset_materialization(
        asset_key="users", metadata={"total_users": total_users}
    )


if __name__ == "__main__":
    # connect to Dagster Pipes
    with open_dagster_pipes():
        main()
