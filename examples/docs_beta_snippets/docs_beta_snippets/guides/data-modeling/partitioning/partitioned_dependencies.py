import dagster as dg
from datetime import datetime, timedelta

# Define partition definitions
daily_partitions = dg.DailyPartitionsDefinition(start_date="2023-01-01")
monthly_partitions = dg.MonthlyPartitionsDefinition(start_date="2023-01-01")

@dg.asset(partitions_def=daily_partitions)
def daily_sales(context):
    # Simulate fetching daily sales data
    date = context.partition_key
    # In a real scenario, you would fetch data for this specific date
    return {"date": date, "sales": 1000}  # Placeholder data

@dg.asset(
    partitions_def=monthly_partitions,
    ins={"daily_sales": dg.AssetIn(partition_mapping={"monthly": "daily"})}
)
def monthly_report(context, daily_sales):
    # Aggregate daily sales into a monthly report
    month_start = datetime.strptime(context.partition_key, "%Y-%m-%d")
    month_end = (month_start.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    
    total_sales = sum(day_data["sales"] for day_data in daily_sales if month_start <= datetime.strptime(day_data["date"], "%Y-%m-%d") <= month_end)
    
    return {
        "month": context.partition_key,
        "total_sales": total_sales
    }



defs = dg.Definitions(
    assets=[daily_sales, monthly_report]
)
