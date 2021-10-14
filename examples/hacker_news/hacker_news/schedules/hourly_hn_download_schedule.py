from datetime import datetime

from dagster import hourly_partitioned_config, hourly_schedule


@hourly_partitioned_config(start_date=datetime(2021, 1, 1))
def hourly_download_schedule_config(start: datetime, end: datetime):
    return {
        "resources": {
            "partition_start": {"config": start.strftime("%Y-%m-%d %H:%M:%S")},
            "partition_end": {"config": end.strftime("%Y-%m-%d %H:%M:%S")},
        }
    }


# legacy


def get_hourly_download_def_schedule_config(start_time: datetime):
    return {
        "resources": {
            "partition_start": {"config": start_time.strftime("%Y-%m-%d %H:00:00")},
            "partition_end": {"config": start_time.strftime("%Y-%m-%d %H:59:59")},
        }
    }


@hourly_schedule(
    pipeline_name="download_pipeline",
    start_date=datetime(2021, 1, 1),
    execution_timezone="UTC",
    mode="prod",
)
def hourly_hn_download_schedule(date):
    """
    This schedule runs the download pipeline once every hour.
    """
    return get_hourly_download_def_schedule_config(date)
