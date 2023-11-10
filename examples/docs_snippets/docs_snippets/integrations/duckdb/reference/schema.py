import pandas as pd

from dagster import SourceAsset, asset

# start_asset_key

daffodil_dataset = SourceAsset(key=["daffodil", "daffodil_dataset"])


@asset(key_prefix=["iris"])
def iris_dataset() -> pd.DataFrame:
    return pd.read_csv(
        "https://docs.dagster.io/assets/iris.csv",
        names=[
            "sepal_length_cm",
            "sepal_width_cm",
            "petal_length_cm",
            "petal_width_cm",
            "species",
        ],
    )


# end_asset_key

# start_metadata

daffodil_dataset = SourceAsset(
    key=["daffodil_dataset"], metadata={"schema": "daffodil"}
)


@asset(metadata={"schema": "iris"})
def iris_dataset() -> pd.DataFrame:
    return pd.read_csv(
        "https://docs.dagster.io/assets/iris.csv",
        names=[
            "sepal_length_cm",
            "sepal_width_cm",
            "petal_length_cm",
            "petal_width_cm",
            "species",
        ],
    )


# end_metadata
