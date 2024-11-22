from typing import List

import pandas as pd

from dagster import AssetIn, Definitions, asset


def store_pandas_dataframe(*_args, **_kwargs):
    pass


def load_pandas_dataframe(*_args, **_kwargs):
    pass


def load_numpy_array(*_args, **_kwargs):
    pass


class PandasSeriesIOManager:
    pass


# start_different_input_managers


@asset
def first_asset() -> list[int]:
    return [1, 2, 3]


@asset
def second_asset() -> list[int]:
    return [4, 5, 6]


@asset(
    ins={
        "first_asset": AssetIn(input_manager_key="pandas_series"),
        "second_asset": AssetIn(input_manager_key="pandas_series"),
    }
)
def third_asset(first_asset: pd.Series, second_asset: pd.Series) -> pd.Series:
    return pd.concat([first_asset, second_asset, pd.Series([7, 8])])


defs = Definitions(
    assets=[first_asset, second_asset, third_asset],
    resources={
        "pandas_series": PandasSeriesIOManager(),
    },
)

# end_different_input_managers
