from datetime import datetime

from dagster import hourly_partitions_def

hourly_partitions = hourly_partitions_def(start_date=datetime(2020, 12, 1))
