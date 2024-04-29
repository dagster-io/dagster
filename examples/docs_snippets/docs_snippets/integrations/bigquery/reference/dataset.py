import pandas as pd

from dagster import AssetsDefinition, asset


def scppe_asset_key():
    # start_asset_key
    daffodil_data = AssetsDefinition.single(
        key=["gcp", "bigquery", "daffodil", "daffodil_data"]
    )

    @asset(key_prefix=["gcp", "bigquery", "iris"])
    def iris_data() -> pd.DataFrame:
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


def scope_metadata():
    # start_metadata
    daffodil_data = AssetsDefinition.single(
        key=["daffodil_data"], metadata={"schema": "daffodil"}
    )

    @asset(metadata={"schema": "iris"})
    def iris_data() -> pd.DataFrame:
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
