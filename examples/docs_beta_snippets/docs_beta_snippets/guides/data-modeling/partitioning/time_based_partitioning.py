import datetime
import os

import pandas as pd

import dagster as dg

# Create the PartitionDefinition,
# which will create a range of partitions from
# 2024-01-01 to the day before the current time
daily_partitions = dg.DailyPartitionsDefinition(start_date="2024-01-01")


# Define the partitioned asset
@dg.asset(partitions_def=daily_partitions)
def daily_sales_data(context: dg.AssetExecutionContext) -> None:
    date = context.partition_key
    # Simulate fetching daily sales data
    df = pd.DataFrame(
        {
            "date": [date] * 10,
            "sales": [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000],
        }
    )

    os.makedirs("data/daily_sales", exist_ok=True)
    filename = f"data/daily_sales/sales_{date}.csv"
    df.to_csv(filename, index=False)

    context.log.info(f"Daily sales data written to {filename}")


@dg.asset(
    partitions_def=daily_partitions,  # Use the daily partitioning scheme
    deps=[daily_sales_data],  # Define dependency on `daily_sales_data` asset
)
def daily_sales_summary(context):
    partition_date_str = context.partition_key
    # Read the CSV file for the given partition date
    filename = f"data/daily_sales/sales_{partition_date_str}.csv"
    df = pd.read_csv(filename)

    # Summarize daily sales
    summary = {
        "date": partition_date_str,
        "total_sales": df["sales"].sum(),
    }

    context.log.info(f"Daily sales summary for {partition_date_str}: {summary}")


# Create a partitioned asset job
daily_sales_job = dg.define_asset_job(
    name="daily_sales_job",
    selection=[daily_sales_data, daily_sales_summary],
)


# Create a schedule to run the job daily
@dg.schedule(
    job=daily_sales_job,
    cron_schedule="0 1 * * *",  # Run at 1:00 AM every day
)
def daily_sales_schedule(context):
    """Process previous day's sales data."""
    # Calculate the previous day's date
    previous_day = context.scheduled_execution_time.date() - datetime.timedelta(days=1)
    date = previous_day.strftime("%Y-%m-%d")
    return dg.RunRequest(
        run_key=date,
        partition_key=date,
    )


# Define the Definitions object
defs = dg.Definitions(
    assets=[daily_sales_data, daily_sales_summary],
    jobs=[daily_sales_job],
    schedules=[daily_sales_schedule],
)
