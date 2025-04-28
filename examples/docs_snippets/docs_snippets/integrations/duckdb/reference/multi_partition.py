def get_iris_data_for_date(*args, **kwargs):
    pass


# start_example

import pandas as pd

import dagster as dg


@dg.asset(
    partitions_def=dg.MultiPartitionsDefinition(
        {
            "date": dg.DailyPartitionsDefinition(start_date="2023-01-01"),
            "species": dg.StaticPartitionsDefinition(
                ["Iris-setosa", "Iris-virginica", "Iris-versicolor"]
            ),
        }
    ),
    metadata={"partition_expr": {"date": "TO_TIMESTAMP(TIME)", "species": "SPECIES"}},
)
def iris_dataset_partitioned(context: dg.AssetExecutionContext) -> pd.DataFrame:
    partition = context.partition_key.keys_by_dimension  # type: ignore
    species = partition["species"]
    date = partition["date"]

    # get_iris_data_for_date fetches all of the iris data for a given date,
    # the returned dataframe contains a column named 'time' with that stores
    # the time of the row as an integer of seconds since epoch
    full_df = get_iris_data_for_date(date)

    return full_df[full_df["species"] == species]


@dg.asset
def iris_cleaned(iris_dataset_partitioned: pd.DataFrame):
    return iris_dataset_partitioned.dropna().drop_duplicates()


# end_example
