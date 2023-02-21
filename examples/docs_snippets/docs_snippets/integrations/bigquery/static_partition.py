# start_example

import pandas as pd

from dagster import StaticPartitionDefinition, asset


@asset(
    partitions_def=StaticPartitionDefinition(["Iris-setosa", "Iris-virginica", "Iris-versicolor"]),
    metadata={"partition_expr": "SPECIES"},
)
def iris_data_partitioned(context) -> pd.DataFrame:
    species = context.asset_partition_key_for_output()

    full_df = pd.read_csv(
        "https://archive.ics.uci.edu/ml/machine-learning-databases/iris/iris.data",
        names=[
            "Sepal length (cm)",
            "Sepal width (cm)",
            "Petal length (cm)",
            "Petal width (cm)",
            "Species",
        ],
    )

    return full_df[full_df["Species"] == species]


@asset
def iris_cleaned(iris_data_partitioned: pd.DataFrame):
    return iris_data_partitioned.dropna().drop_duplicates()


# end_example
