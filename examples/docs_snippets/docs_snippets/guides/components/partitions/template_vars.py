import dagster as dg


@dg.template_var
def the_daily_partitions_def() -> dg.DailyPartitionsDefinition:
    return dg.DailyPartitionsDefinition(start_date="2020-01-01")
