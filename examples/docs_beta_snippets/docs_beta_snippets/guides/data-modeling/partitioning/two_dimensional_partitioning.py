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
    multi_partition_key: dg.MultiPartitionKey = context.partition_key.keys_by_dimension

    # Simulate fetching daily sales data
    df = pd.DataFrame({"date|region": [multi_partition_key], "sales": [1000]})

    os.makedirs("daily_regional_sales", exist_ok=True)
    filename = f"daily_regional_sales/sales_{multi_partition_key}.csv"
    df.to_csv(filename, index=False)

    context.log.info(f"Daily sales data written to {filename}")


@dg.asset(
    partitions_def=two_dimensional_partitions,
    deps=[daily_regional_sales_data],
)
def daily_regional_sales_summary(context):
    multi_partition_key: dg.MultiPartitionKey = context.partition_key.keys_by_dimension
    # Read the CSV file for the given partition date
    filename = f"daily_regional_sales/sales_{multi_partition_key}.csv"
    df = pd.read_csv(filename)

    # Summarize daily sales
    summary = {
        "date|region": multi_partition_key,
        "total_sales": df["sales"].sum(),
    }

    context.log.info(f"Daily sales summary for {multi_partition_key}: {summary}")


# Create a partitioned asset job
daily_regional_sales_job = dg.define_asset_job(
    name="daily_regional_sales_job",
    selection=[daily_regional_sales_data, daily_regional_sales_summary],
    partitions_def=two_dimensional_partitions,
)


# Create a schedule to run the job daily
@dg.schedule(
    job=daily_regional_sales_job,
    cron_schedule="0 1 * * *",  # Run at 1:00 AM every day
)
def daily_regional_sales_schedule(context):
    date = context.scheduled_execution_time.strftime("%Y-%m-%d")
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
