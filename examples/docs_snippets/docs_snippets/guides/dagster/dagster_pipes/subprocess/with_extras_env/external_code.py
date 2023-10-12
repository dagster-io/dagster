# ruff: noqa: T201

import os

import pandas as pd
from dagster_pipes import PipesContext, open_dagster_pipes


def main():
    orders_df = pd.DataFrame({"order_id": [1, 2], "item_id": [432, 878]})
    total_orders = len(orders_df)
    # get the Dagster Pipes context
    pipes = PipesContext.get()
    # get all extras provided by Dagster asset
    print(pipes.extras)
    # get the value of an extra
    print(pipes.get_extra("foo"))
    # get env var
    print(os.environ["MY_ENV_VAR_IN_SUBPROCESS"])


if __name__ == "__main__":
    # connect to Dagster Pipes
    with open_dagster_pipes():
        main()
