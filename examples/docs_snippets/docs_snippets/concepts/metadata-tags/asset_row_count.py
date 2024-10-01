import pandas as pd

from dagster import AssetKey, MaterializeResult, asset


@asset(deps=[AssetKey("source_bar"), AssetKey("source_baz")])
def my_asset():
    my_df: pd.DataFrame = ...

    yield MaterializeResult(metadata={"dagster/row_count": 374})
