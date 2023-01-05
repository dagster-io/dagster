from datetime import datetime

from dagster import HourlyPartitionsDefinition


def compute_static_hourly_partitions(start_date: datetime, end_date: datetime):
    hours_since_end = difference_in_hours(datetime.now(), end_date)
    return HourlyPartitionsDefinition(start_date, end_offset=hours_since_end - 1)


def difference_in_hours(now_date: datetime, then_date: datetime) -> int:
    delta = now_date - then_date
    return (delta.days * 24) + (delta.seconds // 3600)


hourly_partitions = HourlyPartitionsDefinition(start_date=datetime(2023, 1, 5, 20))
# hourly_partitions = StaticPartitionsDefinition(
#     partition_keys=["2023-01-01-00:00", "2023-01-01-01:00"]
# )
# hourly_partitions = compute_static_hourly_partitions(
#     start_date=datetime(2023, 1, 1), end_date=datetime(2023, 1, 1, 3)
# )
# HourlyPartitionsDefinition(start_date=datetime(2023, 1, 1), end_offset=2)
