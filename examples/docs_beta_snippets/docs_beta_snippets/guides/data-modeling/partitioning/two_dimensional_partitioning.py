import datetime
import os

import pandas as pd

import dagster as dg

# Create two PartitionDefinitions
daily_partitions = dg.DailyPartitionsDefinition(start_date="2024-01-01")
region_partitions = dg.StaticPartitionsDefinition(["us", "eu", "jp"])
two_dimensional_partitions = dg.MultiPartitionsDefinition(
    {"date": daily_partitions, "region": region_partitions}
)


# Define the partitioned asset
@dg.asset(partitions_def=two_dimensional_partitions)
def daily_regional_sales_data(context: dg.AssetExecutionContext) -> None:
    # partition_key looks like "2024-01-01|us"
    keys_by_dimension: dg.MultiPartitionKey = context.partition_key.keys_by_dimension

    date = keys_by_dimension["date"]
    region = keys_by_dimension["region"]

    # Simulate fetching daily sales data
    df = pd.DataFrame(
        {
            "date": [date] * 10,
            "region": [region] * 10,
            "sales": [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000],
        }
    )

    os.makedirs("data/daily_regional_sales", exist_ok=True)
    filename = f"data/daily_regional_sales/sales_{context.partition_key}.csv"
    df.to_csv(filename, index=False)

    context.log.info(f"Daily sales data written to {filename}")


@dg.asset(
    partitions_def=two_dimensional_partitions,
    deps=[daily_regional_sales_data],
)
def daily_regional_sales_summary(context):
    # partition_key looks like "2024-01-01|us"
    keys_by_dimension: dg.MultiPartitionKey = context.partition_key.keys_by_dimension

    date = keys_by_dimension["date"]
    region = keys_by_dimension["region"]

    filename = f"data/daily_regional_sales/sales_{context.partition_key}.csv"
    df = pd.read_csv(filename)

    # Summarize daily sales
    summary = {
        "date": date,
        "region": region,
        "total_sales": df["sales"].sum(),
    }

    context.log.info(f"Daily sales summary for {context.partition_key}: {summary}")


# Create a partitioned asset job
daily_regional_sales_job = dg.define_asset_job(
    name="daily_regional_sales_job",
    selection=[daily_regional_sales_data, daily_regional_sales_summary],
)


# Create a schedule to run the job daily
@dg.schedule(
    job=daily_regional_sales_job,
    cron_schedule="0 1 * * *",  # Run at 1:00 AM every day
)
def daily_regional_sales_schedule(context):
    """Process previous day's sales data for all regions."""
    previous_day = context.scheduled_execution_time.date() - datetime.timedelta(days=1)
    date = previous_day.strftime("%Y-%m-%d")

    # Create a run request for each region (3 runs in total every day)
    return [
        dg.RunRequest(
            run_key=f"{date}|{region}",
            partition_key=dg.MultiPartitionKey({"date": date, "region": region}),
        )
        for region in region_partitions.get_partition_keys()
    ]


# Define the Definitions object
defs = dg.Definitions(
    assets=[daily_regional_sales_data, daily_regional_sales_summary],
    jobs=[daily_regional_sales_job],
    schedules=[daily_regional_sales_schedule],
)
