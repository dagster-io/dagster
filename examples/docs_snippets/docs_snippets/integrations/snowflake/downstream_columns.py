import pandas as pd

from dagster import AssetIn, asset

# this example uses the iris_dataset asset from Step 2 of the Using Dagster with Snowflake tutorial


@asset(
    ins={
        "iris_sepal": AssetIn(
            key="iris_dataset",
            metadata={"columns": ["Sepal length (cm)", "Sepal width (cm)"]},
        )
    }
)
def sepal_data(iris_sepal: pd.DataFrame) -> pd.DataFrame:
    iris_sepal["Sepal area (cm2)"] = (
        iris_sepal["Sepal length (cm)"] * iris_sepal["Sepal width (cm)"]
    )
    return iris_sepal
