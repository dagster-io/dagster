import pandas as pd
from dagster_gcp_pandas import BigQueryPandasIOManager

from dagster import Definitions, SourceAsset, asset

iris_harvest_data = SourceAsset(key="iris_harvest_data")


@asset
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


@asset
def iris_cleaned(iris_data: pd.DataFrame) -> pd.DataFrame:
    return iris_data.dropna().drop_duplicates()


defs = Definitions(
    assets=[iris_data, iris_harvest_data, iris_cleaned],
    resources={
        "io_manager": BigQueryPandasIOManager(
            project="my-gcp-project",
            location="us-east5",
            dataset="IRIS",
            timeout=15.0,
        )
    },
)
