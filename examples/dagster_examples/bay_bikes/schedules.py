import os
from datetime import datetime, timedelta

from dagster_examples.bay_bikes.pipelines import generate_training_set_and_train_model

from dagster import daily_schedule, schedules
from dagster.core.definitions.decorators import monthly_schedule
from dagster.utils.merger import dict_merge

weather_etl_environment = generate_training_set_and_train_model.get_preset(
    'weather_etl'
).environment_dict
trip_etl_environment = generate_training_set_and_train_model.get_preset('trip_etl').environment_dict

now = datetime.now()


@daily_schedule(
    pipeline_name='generate_training_set_and_train_model',
    start_date=datetime(year=2019, month=1, day=1),
    execution_time=(now + timedelta(minutes=1)).time(),
    solid_subset=['weather_etl'],
    mode='development',
    environment_vars={'DARK_SKY_API_KEY': os.environ.get('DARK_SKY_API_KEY', '')},
)
def daily_weather_ingest_schedule(date):
    unix_seconds_since_epoch = int((date - datetime(year=1970, month=1, day=1)).total_seconds())
    return dict_merge(
        {
            'resources': weather_etl_environment['resources'],
            'solids': {'weather_etl': weather_etl_environment['solids']['weather_etl']},
        },
        {
            'solids': {
                'weather_etl': {
                    'solids': {
                        'download_weather_report_from_weather_api': {
                            'inputs': {'epoch_date': {'value': unix_seconds_since_epoch}}
                        },
                    },
                }
            }
        },
    )


@daily_schedule(
    pipeline_name='daily_weather_pipeline',
    start_date=datetime(year=2020, month=1, day=1),
    execution_time=(now + timedelta(minutes=1)).time(),
    mode='development',
    environment_vars={'DARK_SKY_API_KEY': os.environ.get('DARK_SKY_API_KEY', '')},
)
def daily_weather_schedule(date):
    unix_seconds_since_epoch = int((date - datetime(year=1970, month=1, day=1)).total_seconds())
    return {
        'resources': weather_etl_environment['resources'],
        'solids': {
            'weather_etl': {
                'solids': {
                    'download_weather_report_from_weather_api': {
                        'inputs': {'epoch_date': {'value': unix_seconds_since_epoch}}
                    },
                    'insert_weather_report_into_table': {
                        'inputs': {'table_name': {'value': 'weather_staging'}}
                    },
                },
            }
        },
    }


@monthly_schedule(
    pipeline_name='generate_training_set_and_train_model',
    start_date=datetime(year=2018, month=1, day=1),
    execution_time=(now + timedelta(minutes=1)).time(),
    execution_day_of_month=now.day,
    solid_subset=['trip_etl'],
    mode='development',
)
def monthly_trip_ingest_schedule(date):
    return dict_merge(
        {
            'resources': trip_etl_environment['resources'],
            'solids': {'trip_etl': trip_etl_environment['solids']['trip_etl']},
        },
        {
            'solids': {
                'trip_etl': {
                    'solids': {
                        'download_baybike_zipfile_from_url': {
                            'inputs': {
                                'file_name': {
                                    'value': '{}-fordgobike-tripdata.csv.zip'.format(
                                        date.date().strftime('%Y%m')
                                    )
                                }
                            }
                        }
                    }
                }
            }
        },
    )


@schedules
def define_scheduler():
    return [daily_weather_ingest_schedule, daily_weather_schedule, monthly_trip_ingest_schedule]
