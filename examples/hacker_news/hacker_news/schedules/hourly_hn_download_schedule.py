from datetime import datetime

from dagster import hourly_partitioned_config


@hourly_partitioned_config(start_date=datetime(2021, 1, 1))
def hourly_download_schedule_config(start: datetime, end: datetime):
    return {
        "resources": {
            "partition_start": {"config": start.strftime("%Y-%m-%d %H:%m:%s")},
            "partition_end": {"config": end.strftime("%Y-%m-%d %H:%m:%s")},
        }
    }
