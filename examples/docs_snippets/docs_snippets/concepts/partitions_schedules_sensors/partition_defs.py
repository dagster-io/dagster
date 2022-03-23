from datetime import datetime

from dagster import (
    daily_partitioned_config,
    hourly_partitioned_config,
    monthly_partitioned_config,
    weekly_partitioned_config,
)

# start_hourly_partition_def


@hourly_partitioned_config(start_date=datetime(2022, 3, 12))
def my_hourly_partitioned_config(start: datetime, _end: datetime):
    return {
        "ops": {
            "process_data_for_date": {"config": {"date": start.strftime("%Y-%m-%d")}}
        }
    }


# end_hourly_partition_def

# start_daily_partition_def


@daily_partitioned_config(start_date="2022-03-12")
def my_daily_partitioned_config(start: datetime, _end: datetime):
    return {
        "ops": {
            "process_data_for_date": {"config": {"date": start.strftime("%Y-%m-%d")}}
        }
    }


# end_daily_partition_def

# start_weekly_partition_def


@weekly_partitioned_config(start_date="2022-03-12")
def my_weekly_partitioned_config(start: datetime, _end: datetime):
    return {
        "ops": {
            "process_data_for_date": {"config": {"date": start.strftime("%Y-%m-%d")}}
        }
    }


# end_weekly_partition_def

# start_monthly_partition_def


@monthly_partitioned_config(start_date="2022-03-12")
def my_monthly_partitioned_config(start: datetime, _end: datetime):
    return {
        "ops": {
            "process_data_for_date": {"config": {"date": start.strftime("%Y-%m-%d")}}
        }
    }


# end_monthly_partition_def

# start_hourly_offset_partition_def


@hourly_partitioned_config(start_date=datetime(2022, 3, 12), minute_offset=15)
def my_hourly_offset_partitioned_config(start: datetime, _end: datetime):
    return {
        "ops": {
            "process_data_for_date": {"config": {"date": start.strftime("%Y-%m-%d")}}
        }
    }


# end_hourly_offset_partition_def

# start_weekly_offset_partition_def


@weekly_partitioned_config(
    start_date="2022-03-12", minute_offset=15, hour_offset=16, day_offset=3
)
def my_weekly_offset_partitioned_config(start: datetime, _end: datetime):
    return {
        "ops": {
            "process_data_for_date": {"config": {"date": start.strftime("%Y-%m-%d")}}
        }
    }


# end_weekly_offset_partition_def

# start_monthly_offset_partition_def


@monthly_partitioned_config(start_date="2022-03-12", day_offset=15)
def my_monthly_offset_partitioned_config(start: datetime, _end: datetime):
    return {
        "ops": {
            "process_data_for_date": {"config": {"date": start.strftime("%Y-%m-%d")}}
        }
    }


# end_monthly_offset_partition_def
