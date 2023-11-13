# start_example

import pandas as pd

from dagster import AssetExecutionContext, StaticPartitionsDefinition, asset


@asset(
    partitions_def=StaticPartitionsDefinition(
        ["Iris-setosa", "Iris-virginica", "Iris-versicolor"]
    ),
    metadata={"partition_expr": "SPECIES"},
)
def iris_data_partitioned(context: AssetExecutionContext) -> pd.DataFrame:
    species = context.asset_partition_key_for_output()

    full_df = pd.read_csv(
        "https://docs.dagster.io/assets/iris.csv",
        names=[
            "sepal_length_cm",
            "sepal_width_cm",
            "petal_length_cm",
            "petal_width_cm",
            "species",
        ],
    )

    return full_df[full_df["species"] == species]


@asset
def iris_cleaned(iris_data_partitioned: pd.DataFrame):
    return iris_data_partitioned.dropna().drop_duplicates()


# end_example
