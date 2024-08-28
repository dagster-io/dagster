import dagster as dg
import pandas as pd


@dg.asset
def iris_dataset_size(context: dg.AssetExecutionContext) -> None:
    df = pd.read_csv(
        "https://docs.dagster.io/assets/iris.csv",
        names=[
            "sepal_length_cm",
            "sepal_width_cm",
            "petal_length_cm",
            "petal_width_cm",
            "species",
        ],
    )

    context.log.info(f"Loaded {df.shape[0]} data points.")


defs = dg.Definitions(assets=[iris_dataset_size])
