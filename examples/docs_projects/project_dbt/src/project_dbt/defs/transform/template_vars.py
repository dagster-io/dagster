import dagster as dg


@dg.template_var
def daily_partitions_def() -> dg.DailyPartitionsDefinition:
    return dg.DailyPartitionsDefinition(start_date="2023-01-01")