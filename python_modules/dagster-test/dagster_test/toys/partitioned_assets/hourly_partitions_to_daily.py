from dagster import DailyPartitionsDefinition, HourlyPartitionsDefinition, asset

hourly_partitions_def = HourlyPartitionsDefinition(start_date="2023-02-01-00:00")
daily_partitions_def = DailyPartitionsDefinition(start_date="2023-02-01")


@asset(partitions_def=hourly_partitions_def)
def hourly_asset1() -> None:
    ...


@asset(partitions_def=hourly_partitions_def)
def hourly_asset2() -> None:
    ...


@asset(partitions_def=daily_partitions_def, deps=[hourly_asset1, hourly_asset2])
def daily_asset() -> None:
    ...
