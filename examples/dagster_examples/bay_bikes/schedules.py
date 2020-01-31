import os
from datetime import datetime, timedelta

from dagster_cron import SystemCronScheduler

from dagster import daily_schedule, schedules
from dagster.core.definitions.decorators import monthly_schedule

now = datetime.now()


@daily_schedule(
    pipeline_name='extract_daily_weather_data_pipeline',
    start_date=datetime(year=2019, month=1, day=1),
    execution_time=(now + timedelta(minutes=1)).time(),
    mode='development',
    environment_vars={'DARK_SKY_API_KEY': os.environ.get('DARK_SKY_API_KEY', '')},
)
def daily_weather_ingest_schedule(date):
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


@monthly_schedule(
    pipeline_name='monthly_trip_pipeline',
    start_date=datetime(year=2018, month=1, day=1),
    execution_time=(now + timedelta(minutes=1)).time(),
    execution_day_of_month=now.day,
    mode='development',
)
def monthly_trip_ingest_schedule(date):
    return {
        'resources': {
            'postgres_db': {
                'config': {
                    'postgres_db_name': 'test',
                    'postgres_hostname': 'localhost',
                    'postgres_password': 'test',
                    'postgres_username': 'test',
                }
            },
            'volume': {'config': {'mount_location': '/tmp'}},
        },
        'solids': {
            'download_baybike_zipfile_from_url': {
                'inputs': {
                    'file_name': {
                        'value': '{}-fordgobike-tripdata.csv.zip'.format(
                            date.date().strftime('%Y%m')
                        )
                    },
                    'base_url': {'value': 'https://s3.amazonaws.com/baywheels-data'},
                }
            },
            'load_baybike_data_into_dataframe': {
                'inputs': {
                    'target_csv_file_in_archive': {
                        'value': '{}-fordgobike-tripdata.csv'.format(date.date().strftime('%Y%m'))
                    }
                }
            },
            'insert_trip_data_into_table': {
                'config': {'index_label': 'uuid'},
                'inputs': {'table_name': 'trips'},
            },
        },
    }


@schedules(scheduler=SystemCronScheduler)
def define_scheduler():
    return [daily_weather_ingest_schedule, monthly_trip_ingest_schedule]
