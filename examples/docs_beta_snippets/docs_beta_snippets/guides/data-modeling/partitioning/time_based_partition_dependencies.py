import os

import pandas as pd

import dagster as dg

# Create the PartitionDefinition
daily_partitions = dg.DailyPartitionsDefinition(start_date="2024-01-01")


# Define the partitioned asset
@dg.asset(partitions_def=daily_partitions)
def daily_sales_data(context: dg.AssetExecutionContext) -> None:
    date = context.partition_key
    # Simulate fetching daily sales data
    df = pd.DataFrame({"date": [date], "sales": [1000]})

    os.makedirs("daily_sales", exist_ok=True)
    filename = f"daily_sales/sales_{date}.csv"
    df.to_csv(filename, index=False)

    context.log.info(f"Daily sales data written to {filename}")


@dg.asset(
    partitions_def=daily_partitions,
    deps=[daily_sales_data],
)
def monthly_sales_summary(context):
    

# Create a partitioned asset job
daily_sales_job = dg.define_asset_job(
    name="daily_sales_job",
    selection=[daily_sales_data, daily_sales_summary],
    partitions_def=daily_partitions,
)


# Create a schedule to run the job daily
@dg.schedule(
    job=daily_sales_job,
    cron_schedule="0 1 * * *",  # Run at 1:00 AM every day
)
def daily_sales_schedule(context):
    date = context.scheduled_execution_time.strftime("%Y-%m-%d")
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
