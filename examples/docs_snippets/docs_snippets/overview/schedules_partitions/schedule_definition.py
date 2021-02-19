from datetime import datetime

from dagster import daily_schedule, hourly_schedule, monthly_schedule, schedule, weekly_schedule


# start_def
@schedule(
    cron_schedule="0 1 * * *", pipeline_name="my_data_pipeline", execution_timezone="US/Central"
)  # Executes at 1:00 AM in US/Central time every day
def my_schedule(context):
    date = context.scheduled_execution_time.strftime("%Y-%m-%d")
    return {"solids": {"process_data_for_date": {"config": {"date": date}}}}


# end_def

# start_part
@hourly_schedule(
    pipeline_name="my_data_pipeline",
    start_date=datetime(2020, 1, 1),
    execution_timezone="US/Central",
)
def my_hourly_schedule(date):
    return {
        "solids": {
            "process_data_for_date": {"config": {"date": date.strftime("%Y-%m-%d %H:%M:%S")}}
        }
    }


@daily_schedule(
    pipeline_name="my_data_pipeline",
    start_date=datetime(2020, 1, 1),
    execution_timezone="US/Central",
)
def my_daily_schedule(date):
    return {"solids": {"process_data_for_date": {"config": {"date": date.strftime("%Y-%m-%d")}}}}


@weekly_schedule(
    pipeline_name="my_data_pipeline",
    start_date=datetime(2020, 1, 1),
    execution_timezone="US/Central",
    partition_weeks_offset=2,  # Use the partition for two weeks ago, not last week
)
def my_weekly_schedule(date):
    return {"solids": {"process_data_for_date": {"config": {"date": date.strftime("%Y-%m-%d")}}}}


@monthly_schedule(
    pipeline_name="my_data_pipeline",
    start_date=datetime(2020, 1, 1),
    execution_timezone="US/Central",
    partition_months_offset=0,  # Use the partition for the current month, not the previous month
)
def my_monthly_schedule(date):
    return {"solids": {"process_data_for_date": {"config": {"date": date.strftime("%Y-%m-%d")}}}}


# end_part

# start_timezone
@daily_schedule(
    pipeline_name="my_data_pipeline",
    start_date=datetime(2020, 1, 1),
    execution_time=datetime.time(9, 0),
    execution_timezone="US/Pacific",
)
def my_timezone_schedule(date):
    return {"solids": {"process_data_for_date": {"config": {"date": date.strftime("%Y-%m-%d")}}}}


# end_timezone
