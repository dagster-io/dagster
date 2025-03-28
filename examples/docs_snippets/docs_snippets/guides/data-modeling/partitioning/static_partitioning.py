import os

import pandas as pd

import dagster as dg

# Create the PartitionDefinition
region_partitions = dg.StaticPartitionsDefinition(["us", "eu", "jp"])


# Define the partitioned asset
@dg.asset(partitions_def=region_partitions)  # Use the region partitioning scheme
def regional_sales_data(context: dg.AssetExecutionContext) -> None:
    region = context.partition_key

    # Simulate fetching daily sales data
    df = pd.DataFrame(
        {
            "region": [region] * 10,
            "sales": [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000],
        }
    )

    os.makedirs("data/regional_sales", exist_ok=True)
    filename = f"data/regional_sales/sales_{region}.csv"
    df.to_csv(filename, index=False)

    context.log.info(f"Regional sales data written to {filename}")


@dg.asset(
    partitions_def=region_partitions,  # Use the region partitioning scheme
    deps=[regional_sales_data],
)
def daily_sales_summary(context):
    region = context.partition_key
    # Read the CSV file for the given partition date
    filename = f"data/regional_sales/sales_{region}.csv"
    df = pd.read_csv(filename)

    # Summarize daily sales
    summary = {
        "region": region,
        "total_sales": df["sales"].sum(),
    }

    context.log.info(f"Regional sales summary for {region}: {summary}")


# Create a partitioned asset job
regional_sales_job = dg.define_asset_job(
    name="regional_sales_job",
    selection=[regional_sales_data, daily_sales_summary],
)


# Define the Definitions object
defs = dg.Definitions(
    assets=[regional_sales_data, daily_sales_summary],
    jobs=[regional_sales_job],
)
