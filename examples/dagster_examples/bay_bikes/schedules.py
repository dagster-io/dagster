import os
from datetime import datetime, timedelta

from dagster_cron import SystemCronScheduler

from dagster import daily_schedule, schedules

RESOURCE_CREDENTIALS = ['DARK_SKY_API_KEY', 'GOOGLE_APPLICATION_CREDENTIALS']


@daily_schedule(
    pipeline_name='extract_daily_weather_data_pipeline',
    start_date=datetime(year=2019, month=1, day=1),
    execution_time=(datetime.now() + timedelta(minutes=1)).time(),
    mode='development',
    environment_vars={cred_name: os.environ.get(cred_name) for cred_name in RESOURCE_CREDENTIALS},
)
def daily_ingest_schedule(date):
    unix_seconds_since_epoch = int((date - datetime(year=1970, month=1, day=1)).total_seconds())
    return {
        "resources": {
            "credentials_vault": {"config": {"environment_variable_names": ["DARK_SKY_API_KEY"]}},
            "postgres_db": {
                "config": {
                    "postgres_db_name": "test",
                    "postgres_hostname": "localhost",
                    "postgres_password": "test",
                    "postgres_username": "test",
                }
            },
        },
        "solids": {
            "download_weather_report_from_weather_api": {
                "inputs": {"epoch_date": {"value": unix_seconds_since_epoch}}
            },
            "insert_weather_report_into_table": {
                "config": {"index_label": "uuid"},
                "inputs": {"table_name": {"value": "weather"}},
            },
        },
    }


@schedules(scheduler=SystemCronScheduler)
def define_scheduler():
    return [daily_ingest_schedule]
