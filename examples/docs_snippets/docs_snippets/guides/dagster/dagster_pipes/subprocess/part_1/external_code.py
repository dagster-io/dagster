# ruff: noqa: T201
import pandas as pd


# start_external_code
def main():
    orders_df = pd.DataFrame({"order_id": [1, 2], "item_id": [432, 878]})
    total_orders = len(orders_df)
    print(f"processing total {total_orders} orders")


# end_external_code


if __name__ == "__main__":
    main()
