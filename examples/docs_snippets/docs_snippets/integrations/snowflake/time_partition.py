get_iris_data_for_date = None

# start_example

import pandas as pd

from dagster import DailyPartitionsDefinition, asset


@asset(
    partitions_def=DailyPartitionsDefinition(start_date="2023-01-01"),
    metadata={"partition_expr": "DATE"},
)
def iris_data_per_day(context) -> pd.DataFrame:
    partition = context.asset_partition_key_for_output()

    # get_iris_data_for_date fetches all of the iris data for a given date,
    # the returned dataframe contains a column named 'date' with date data in the
    # form YYYY-MM-DD
    return get_iris_data_for_date(partition)


# end_example
