get_iris_data_for_date = None

# start_example

import pandas as pd

from dagster import DailyPartitionsDefinition, asset


@asset(
    partitions_def=DailyPartitionsDefinition(start_date="2023-01-01"),
    metadata={"partition_expr": "TO_TIMESTAMP(time::INT)"},
)
def iris_data_per_day(context) -> pd.DataFrame:
    partition = context.asset_partition_key_for_output()

    # get_iris_data_for_date fetches all of the iris data for a given date,
    # the returned dataframe contains a column named 'time' with that stores
    # the time of the row as an integer of seconds since epoch
    return get_iris_data_for_date(partition)


# end_example
