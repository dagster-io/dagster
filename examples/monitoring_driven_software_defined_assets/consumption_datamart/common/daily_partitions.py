from datetime import datetime, timedelta

from dagster import DailyPartitionsDefinition

PARTITION_START = datetime(2021, 12, 1)
PARTITION_END = PARTITION_START + timedelta(days=7)

daily_partitions = DailyPartitionsDefinition(
    start_date=PARTITION_START,
    timezone="UTC",
    end_offset=(PARTITION_END - datetime.utcnow()).days  # effective end_date => PARTITION_END
)
