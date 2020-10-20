import os
from datetime import datetime, timedelta

from dagster import daily_schedule
from dagster.core.definitions.decorators import monthly_schedule
from dagster.utils.merger import deep_merge_dicts
from dagster_examples.bay_bikes.pipelines import generate_training_set_and_train_model

weather_etl_environment = generate_training_set_and_train_model.get_preset(
    "prod_weather_etl"
).run_config
trip_etl_environment = generate_training_set_and_train_model.get_preset("prod_trip_etl").run_config

now = datetime.now()


@daily_schedule(
    pipeline_name="generate_training_set_and_train_model",
    start_date=datetime(year=2019, month=1, day=1),
    execution_time=(now + timedelta(minutes=1)).time(),
    solid_selection=["weather_etl"],
    mode="production",
    environment_vars={
        "POSTGRES_USERNAME": os.environ.get("POSTGRES_USERNAME", ""),
        "POSTGRES_PASSWORD": os.environ.get("POSTGRES_PASSWORD", ""),
        "POSTGRES_HOST": os.environ.get("POSTGRES_HOST", ""),
        "POSTGRES_DB": os.environ.get("POSTGRES_DB", ""),
    },
)
def daily_weather_ingest_schedule(date):
    unix_seconds_since_epoch = int((date - datetime(year=1970, month=1, day=1)).total_seconds())
    return deep_merge_dicts(
        {
            "solids": {
                "weather_etl": {
                    "solids": {
                        "download_weather_report_from_weather_api": {
                            "inputs": {"epoch_date": {"value": unix_seconds_since_epoch}}
                        },
                    },
                }
            }
        },
        {
            "resources": weather_etl_environment["resources"],
            "solids": {"weather_etl": weather_etl_environment["solids"]["weather_etl"]},
        },
    )


@daily_schedule(
    pipeline_name="daily_weather_pipeline",
    start_date=datetime(year=2020, month=1, day=1),
    execution_time=(now + timedelta(minutes=1)).time(),
    mode="production",
    environment_vars={
        "DARK_SKY_API_KEY": os.environ.get("DARK_SKY_API_KEY", ""),
        "POSTGRES_USERNAME": os.environ.get("POSTGRES_USERNAME", ""),
        "POSTGRES_PASSWORD": os.environ.get("POSTGRES_PASSWORD", ""),
        "POSTGRES_HOST": os.environ.get("POSTGRES_HOST", ""),
        "POSTGRES_DB": os.environ.get("POSTGRES_DB", ""),
    },
)
def daily_weather_schedule(date):
    unix_seconds_since_epoch = int((date - datetime(year=1970, month=1, day=1)).total_seconds())
    return {
        "resources": weather_etl_environment["resources"],
        "solids": {
            "weather_etl": {
                "solids": {
                    "download_weather_report_from_weather_api": {
                        "inputs": {"epoch_date": {"value": unix_seconds_since_epoch}}
                    },
                    "insert_weather_report_into_table": {
                        "inputs": {"table_name": {"value": "weather_staging"}}
                    },
                },
            }
        },
    }


@monthly_schedule(
    pipeline_name="generate_training_set_and_train_model",
    start_date=datetime(year=2018, month=1, day=1),
    execution_time=(now + timedelta(minutes=1)).time(),
    execution_day_of_month=now.day,
    solid_selection=["trip_etl"],
    mode="production",
    environment_vars={
        "POSTGRES_USERNAME": os.environ.get("POSTGRES_USERNAME", ""),
        "POSTGRES_PASSWORD": os.environ.get("POSTGRES_PASSWORD", ""),
        "POSTGRES_HOST": os.environ.get("POSTGRES_HOST", ""),
        "POSTGRES_DB": os.environ.get("POSTGRES_DB", ""),
    },
)
def monthly_trip_ingest_schedule(date):
    return deep_merge_dicts(
        {
            "solids": {
                "trip_etl": {
                    "solids": {
                        "download_baybike_zipfile_from_url": {
                            "inputs": {
                                "file_name": {
                                    "value": "{}-fordgobike-tripdata.csv.zip".format(
                                        date.date().strftime("%Y%m")
                                    )
                                }
                            }
                        }
                    }
                }
            }
        },
        {
            "resources": trip_etl_environment["resources"],
            "solids": {"trip_etl": trip_etl_environment["solids"]["trip_etl"]},
        },
    )


def define_schedules():
    return {
        "daily_weather_ingest_schedule": lambda: daily_weather_ingest_schedule,
        "daily_weather_schedule": lambda: daily_weather_schedule,
        "monthly_trip_ingest_schedule": lambda: monthly_trip_ingest_schedule,
    }
