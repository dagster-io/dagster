import os
import urllib.request

# Create a new 'nasa' directory if needed
dir_name = "nasa"
if not os.path.exists(dir_name):
    os.makedirs(dir_name)

from dagster import AssetExecutionContext, DailyPartitionsDefinition, asset


@asset(partitions_def=DailyPartitionsDefinition(start_date="2023-10-01"))
def my_daily_partitioned_asset(context: AssetExecutionContext) -> None:
    partition_date_str = context.asset_partition_key_for_output()

    url = f"https://api.nasa.gov/planetary/apod?api_key=DEMO_KEY&date={partition_date_str}"
    target_location = f"nasa/{partition_date_str}.csv"

    urllib.request.urlretrieve(url, target_location)
