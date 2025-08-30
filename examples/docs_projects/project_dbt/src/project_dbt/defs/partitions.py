import dagster as dg

START_DATE = "2023-01-01"
END_DATE = "2023-04-01"

daily_partition = dg.DailyPartitionsDefinition(start_date=START_DATE, end_date=END_DATE)

monthly_partition = dg.MonthlyPartitionsDefinition(start_date=START_DATE, end_date=END_DATE)
