import pandas as pd
from dagster_pipes import PipesContext, open_dagster_pipes


def main():
    orders_df = pd.DataFrame({"order_id": [1, 2], "item_id": [432, 878]})
    total_orders = len(orders_df)
    # get the Dagster Pipes context
    pipes = PipesContext.get()
    # send structured metadata back to Dagster
    pipes.report_asset_materialization(metadata={"total_orders": total_orders})
    # report data quality check result back to Dagster
    pipes.report_asset_check(
        passed=orders_df[["item_id"]].notnull().all().bool(),
        check_name="no_empty_order_check",
    )


if __name__ == "__main__":
    # connect to Dagster Pipes
    with open_dagster_pipes():
        main()
