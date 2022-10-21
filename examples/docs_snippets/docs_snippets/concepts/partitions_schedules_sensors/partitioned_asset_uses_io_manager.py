import pandas as pd

from dagster import DailyPartitionsDefinition, asset


@asset(partitions_def=DailyPartitionsDefinition(start_date="2022-01-01"))
def my_daily_partitioned_asset(context) -> pd.DataFrame:
    partition_date_str = context.asset_partition_key_for_output()
    return pd.read_csv(f"coolweatherwebsite.com/weather_obs&date={partition_date_str}")
