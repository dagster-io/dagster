import datetime
import os

import pandas as pd

import dagster as dg

# Create the PartitionDefinition
daily_partitions = dg.DailyPartitionsDefinition(start_date="2024-01-01")
weekly_partitions = dg.WeeklyPartitionsDefinition(start_date="2024-01-01")


# Define the partitioned asset
@dg.asset(partitions_def=daily_partitions)
def daily_sales_data(context: dg.AssetExecutionContext):
    date = context.partition_key
    # Simulate fetching daily sales data
    df = pd.DataFrame({"date": [date], "sales": [1000]})

    os.makedirs("data/daily_sales", exist_ok=True)
    filename = f"data/daily_sales/sales_{date}.csv"
    df.to_csv(filename, index=False)

    context.log.info(f"Daily sales data written to {filename}")


@dg.asset(
    partitions_def=weekly_partitions,
    deps=[
        dg.AssetDep(
            "daily_sales_data",
            partition_mapping=dg.TimeWindowPartitionMapping(),
        )
    ],
)
def weekly_sales_summary(context: dg.AssetExecutionContext):
    week = context.partition_key
    partition_key_range = context.asset_partition_key_range_for_input(
        "daily_sales_data"
    )
    start_date = partition_key_range.start
    end_date = partition_key_range.end
    context.log.info(f"start_date: {start_date}, end_date: {end_date}")

    df = pd.DataFrame()
    for date in pd.date_range(start_date, end_date):
        filename = f"data/daily_sales/sales_{date.strftime('%Y-%m-%d')}.csv"
        df = pd.concat([df, pd.read_csv(filename)])
        context.log.info(f"df: {df}")

    weekly_summary = {
        "week": week,
        "total_sales": df["sales"].sum(),
    }

    context.log.info(f"weekly sales summary for {week}: {weekly_summary}")


# Define the Definitions object
defs = dg.Definitions(
    assets=[daily_sales_data, weekly_sales_summary],
)
