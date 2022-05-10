from datetime import datetime

from dagster import hourly_partitioned_config


@hourly_partitioned_config(start_date=datetime(2020, 12, 1))
def hourly_download_config(start: datetime, end: datetime):
    return {
        "resources": {
            "partition_bounds": {
                "config": {
                    "start": start.strftime("%Y-%m-%d %H:%M:%S"),
                    "end": end.strftime("%Y-%m-%d %H:%M:%S"),
                }
            },
        }
    }
