# start_asset_key

import pandas as pd

from dagster import SourceAsset, asset

daffodil_data = SourceAsset(key=["gcp", "bigquery", "daffodil", "daffodil_data"])


@asset(key_prefix=["gcp", "bigquery", "iris"])
def iris_data() -> pd.DataFrame:
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
