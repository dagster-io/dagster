from datetime import datetime

from dagster import HourlyPartitionsDefinition

hourly_partitions = HourlyPartitionsDefinition(start_date=datetime(2020, 12, 1))
