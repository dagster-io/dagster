import pandas as pd
from dagster_pipes import PipesContext, open_dagster_pipes


def main():
    # get the Dagster Pipes context
    context = PipesContext.get()

    # compute the full orders data
    orders = pd.DataFrame(
        {
            "order_id": [1, 2, 3],
            "item_id": [321, 654, 987],
            "order_details": [..., ..., ...],  # imagine large data,
            # and more columns
        }
    )

    # send a smaller table to be I/O managed by Dagster and passed to downstream assets
    summary_table = pd.DataFrame(orders[["order_id", "item_id"]])
    context.report_custom_message(summary_table.to_dict())

    context.report_asset_materialization(metadata={"total_orders": len(orders)})


if __name__ == "__main__":
    # connect to Dagster Pipes
    with open_dagster_pipes():
        main()
