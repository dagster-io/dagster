get_iris_data_for_date = None

# start_example

import pandas as pd

from dagster import (
    DailyPartitionsDefinition,
    MultiPartitionsDefinition,
    StaticPartitionDefinition,
    asset,
)


@asset(
    partitions_def=MultiPartitionsDefinition(
        {
            "date": DailyPartitionsDefinition(start_date="2023-01-01"),
            "species": StaticPartitionDefinition(
                ["Iris-setosa", "Iris-virginica", "Iris-versicolor"]
            ),
        }
    ),
    metadata={"partition_expr": {"species": "SPECIES", "date": "DATE"}},
)
def iris_dataset_partitioned(context) -> pd.DataFrame:
    partition = partition = context.partition_key.keys_by_dimension
    species = partition["species"]
    date = partition["date"]

    # get_iris_data_for_date fetches all of the iris data for a given date,
    # the returned dataframe contains a column named 'date' with date data in the
    # form YYYY-MM-DD
    full_df = get_iris_data_for_date(date)

    return full_df[full_df["Species"] == species]


# end_example
