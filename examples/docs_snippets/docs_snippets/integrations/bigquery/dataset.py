# start_asset_key

import pandas as pd

from dagster import SourceAsset, asset

daffodil_data = SourceAsset(key=["gcp", "bigquery", "daffodil", "daffodil_data"])


@asset(key_prefix=["gcp", "bigquery", "iris"])
def iris_data() -> pd.DataFrame:
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
