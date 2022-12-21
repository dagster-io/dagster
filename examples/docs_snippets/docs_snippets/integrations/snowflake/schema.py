# start_asset_key

import pandas as pd

from dagster import SourceAsset, asset

daffodil_dataset = SourceAsset(key=["daffodil", "daffodil_dataset"])


@asset(key_prefix=["iris"])
def iris_dataset() -> pd.DataFrame:
    return pd.read_csv(
        "https://archive.ics.uci.edu/ml/machine-learning-databases/iris/iris.data",
        names=[
            "Sepal length (cm)",
            "Sepal width (cm)",
            "Petal length (cm)",
            "Petal width (cm)",
            "Species",
        ],
    )


# end_asset_key
