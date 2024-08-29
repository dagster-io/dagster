import dagster as dg
from datetime import datetime, timedelta

import urllib3

# Create the PartitionDefinition
daily_partitions = dg.DailyPartitionsDefinition(start_date="2024-01-01")

# Define the partitioned asset
@dg.asset(partitions_def=daily_partitions)
def my_daily_partitioned_asset(context: dg.AssetExecutionContext) -> None:
    partition_date_str = context.partition_key

    url = f"https://api.nasa.gov/planetary/apod?api_key=DEMO_KEY&date={partition_date_str}"
    target_location = f"nasa/{partition_date_str}.csv"

    urllib3.request.request.urlretrieve(url, target_location)

# Create a schedule to run the job daily
@dg.schedule(
    job=materialize_logs,
    cron_schedule="0 1 * * *",  # Run at 1:00 AM every day
)
def daily_log_schedule(context):
    date = context.scheduled_execution_time.strftime("%Y-%m-%d")
    return dg.RunRequest(
        run_key=date,
        partition_key=date,
    )

# Define the Definitions object
defs = dg.Definitions(
    assets=[daily_logs],
    jobs=[materialize_logs],
    schedules=[daily_log_schedule],
)

if __name__ == "__main__":
    # Execute the job for a specific date
    result = materialize_logs.execute_in_process(
        partition_key="2023-05-15",
        run_config={},
    )
    print(result.success)
    print(result.return_value)