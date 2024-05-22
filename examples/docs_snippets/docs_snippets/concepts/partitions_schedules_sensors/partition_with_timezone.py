from dagster import DailyPartitionsDefinition

daily_partition = DailyPartitionsDefinition(
    start_date="2024-05-20", timezone="America/Los_Angeles"
)
