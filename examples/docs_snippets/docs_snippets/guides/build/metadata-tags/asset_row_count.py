import pandas as pd

import dagster as dg


@dg.asset(deps=[dg.AssetKey("source_bar"), dg.AssetKey("source_baz")])
def my_asset():
    my_df: pd.DataFrame = ...  # ty: ignore[invalid-assignment]

    yield dg.MaterializeResult(metadata={"dagster/row_count": 374})
