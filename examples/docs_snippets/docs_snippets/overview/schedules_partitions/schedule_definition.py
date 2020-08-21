from datetime import datetime

from dagster import daily_schedule, hourly_schedule, monthly_schedule, schedule, weekly_schedule


@schedule(
    cron_schedule="0 0 * * *", pipeline_name="my_data_pipeline"
)  # Executes at 1:00 AM every day
def my_schedule():
    date = datetime.today().strftime("%Y-%m-%d")
    return {"solids": {"process_data_for_date": {"config": {"date": date}}}}


@hourly_schedule(pipeline_name="my_data_pipeline", start_date=datetime(2020, 1, 1))
def my_hourly_schedule(date):
    return {
        "solids": {
            "process_data_for_date": {"config": {"date": date.strftime("%Y-%m-%d %H:%M:%S")}}
        }
    }


@daily_schedule(pipeline_name="my_data_pipeline", start_date=datetime(2020, 1, 1))
def my_daily_schedule(date):
    return {"solids": {"process_data_for_date": {"config": {"date": date.strftime("%Y-%m-%d")}}}}


@weekly_schedule(pipeline_name="my_data_pipeline", start_date=datetime(2020, 1, 1))
def my_weekly_schedule(date):
    return {"solids": {"process_data_for_date": {"config": {"date": date.strftime("%Y-%m-%d")}}}}


@monthly_schedule(pipeline_name="my_data_pipeline", start_date=datetime(2020, 1, 1))
def my_monthly_schedule(date):
    return {"solids": {"process_data_for_date": {"config": {"date": date.strftime("%Y-%m-%d")}}}}
