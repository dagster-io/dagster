from datetime import datetime

from dagster import hourly_schedule


@hourly_schedule(
    pipeline_name="download_pipeline",
    start_date=datetime(2021, 1, 1),
    execution_timezone="UTC",
    mode="prod",
)
def hourly_hn_download_schedule(start_time):
    """
    This schedule runs the download pipeline once every hour.
    """
    return {
        "resources": {
            "partition_start": {"config": start_time.strftime("%Y-%m-%d %H:00:00")},
            "partition_end": {"config": start_time.strftime("%Y-%m-%d %H:59:59")},
        }
    }
