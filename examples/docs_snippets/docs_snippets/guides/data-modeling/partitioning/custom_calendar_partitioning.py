from datetime import datetime

import dagster as dg

# Define your market holidays
market_holidays_2024_strings = [
    "2024-01-01",  # New Year's Day
    "2024-01-15",  # Martin Luther King Jr. Day
    "2024-02-19",  # Presidents Day
    "2024-03-29",  # Good Friday
    "2024-05-27",  # Memorial Day
    "2024-06-19",  # Juneteenth
    "2024-07-04",  # Independence Day
    "2024-09-02",  # Labor Day
    "2024-11-28",  # Thanksgiving
    "2024-12-25",  # Christmas Day
]

exclusions = [
    datetime.strptime(date_str, "%Y-%m-%d") for date_str in market_holidays_2024_strings
]

# Create weekday partitions excluding holidays
market_calendar = dg.TimeWindowPartitionsDefinition(
    start=datetime(2024, 1, 1),
    cron_schedule="0 0 * * 1-5",  # Weekdays only
    fmt="%Y-%m-%d",
    # Exclude specific holiday dates
    exclusions=exclusions,
)


@dg.asset(partitions_def=market_calendar)
def market_data(context: dg.AssetExecutionContext):
    trading_date = context.partition_key
    context.log.info(f"Processing market data for trading day: {trading_date}")
