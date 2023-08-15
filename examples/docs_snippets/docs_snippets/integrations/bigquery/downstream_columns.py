import pandas as pd

from dagster import AssetIn, asset

# this example uses the iris_data asset from Step 2 of the Using Dagster with BigQuery tutorial


@asset(
    ins={
        "iris_sepal": AssetIn(
            key="iris_data",
            metadata={"columns": ["sepal_length_cm", "sepal_width_cm"]},
        )
    }
)
def sepal_data(iris_sepal: pd.DataFrame) -> pd.DataFrame:
    iris_sepal["sepal_area_cm2"] = (
        iris_sepal["sepal_length_cm"] * iris_sepal["sepal_width_cm"]
    )
    return iris_sepal
