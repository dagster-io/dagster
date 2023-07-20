import urllib.request

from dagster import AssetExecutionContext, DailyPartitionsDefinition, asset


@asset(partitions_def=DailyPartitionsDefinition(start_date="2022-01-01"))
def my_daily_partitioned_asset(context: AssetExecutionContext) -> None:
    partition_date_str = context.asset_partition_key_for_output()

    url = f"coolweatherwebsite.com/weather_obs&date={partition_date_str}"
    target_location = f"weather_observations/{partition_date_str}.csv"

    urllib.request.urlretrieve(url, target_location)
