import datetime

from dagster import daily_schedule, schedule

# start_partition_based_schedule


@daily_schedule(
    pipeline_name="my_pipeline",
    start_date=datetime.datetime(2021, 1, 1),
    execution_time=datetime.time(11, 0),
    execution_timezone="US/Central",
)
def my_daily_schedule(date):
    return {"solids": {"process_data_for_date": {"config": {"date": date.strftime("%Y-%m-%d")}}}}


# end_partition_based_schedule


# start_non_partition_based_schedule


@schedule(cron_schedule="0 1 * * *", pipeline_name="my_pipeline", execution_timezone="US/Central")
def my_schedule():
    return {"solids": {"process_data": {"config": {"dataset_name": "my_dataset"}}}}


# end_non_partition_based_schedule


# start_execution_time


@schedule(cron_schedule="0 1 * * *", pipeline_name="my_pipeline", execution_timezone="US/Central")
def my_execution_time_schedule(context):
    date = context.scheduled_execution_time.strftime("%Y-%m-%d")
    return {
        "solids": {
            "process_data": {"config": {"dataset_name": "my_dataset", "execution_date": date}}
        }
    }


# end_execution_time

# start_timezone


@daily_schedule(
    pipeline_name="my_data_pipeline",
    start_date=datetime.datetime(2020, 1, 1),
    execution_time=datetime.time(9, 0),
    execution_timezone="US/Pacific",
)
def my_timezone_schedule(date):
    return {
        "solids": {
            "process_data_for_date": {"config": {"date": date.strftime("%Y-%m-%d %H:%M:%S")}}
        }
    }


# end_timezone
