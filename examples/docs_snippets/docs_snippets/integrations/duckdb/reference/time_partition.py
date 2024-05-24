def get_iris_data_for_date(*args, **kwargs):
    pass


# start_example

import pandas as pd

from dagster import AssetExecutionContext, DailyPartitionsDefinition, asset


@asset(
    partitions_def=DailyPartitionsDefinition(start_date="2023-01-01"),
    metadata={"partition_expr": "TO_TIMESTAMP(TIME)"},
)
def iris_data_per_day(context: AssetExecutionContext) -> pd.DataFrame:
    partition = context.partition_key

    # get_iris_data_for_date fetches all of the iris data for a given date,
    # the returned dataframe contains a column named 'time' with that stores
    # the time of the row as an integer of seconds since epoch
    return get_iris_data_for_date(partition)


@asset
def iris_cleaned(iris_data_per_day: pd.DataFrame):
    return iris_data_per_day.dropna().drop_duplicates()


# end_example
