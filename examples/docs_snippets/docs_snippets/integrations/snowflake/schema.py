# start_asset_key

import pandas as pd

from dagster import SourceAsset, asset

daffodil_dataset = SourceAsset(key=["daffodil", "daffodil_dataset"])


@asset(key_prefix=["iris"])
def iris_dataset() -> pd.DataFrame:
    return pd.read_csv(
        "https://archive.ics.uci.edu/ml/machine-learning-databases/iris/iris.data",
        names=[
            "sepal_length_cm",
            "sepal_width_cm",
            "petal_length_cm",
            "petal_width_cm",
            "species",
        ],
    )


# end_asset_key
