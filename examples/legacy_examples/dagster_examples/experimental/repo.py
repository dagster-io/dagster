# pylint: disable=no-value-for-parameter

import datetime

from dagster import (
    PresetDefinition,
    daily_schedule,
    hourly_schedule,
    pipeline,
    repository,
    schedule,
    solid,
)


@hourly_schedule(
    pipeline_name="metrics_pipeline",
    start_date=datetime.datetime(2019, 12, 1),
    execution_time=datetime.time(),
)
def daily_ingest_schedule(date):
    date_path = date.strftime("%Y/%m/%d/%H")
    return {
        "solids": {
            "save_metrics": {
                "inputs": {"data_path": {"value": "s3://bucket-name/data/{}".format(date_path)}}
            }
        },
    }


@daily_schedule(
    pipeline_name="rollup_pipeline",
    start_date=datetime.datetime(2019, 12, 1),
    execution_time=datetime.time(hour=3, minute=0),
)
def daily_rollup_schedule(date):
    date_path = date.strftime("%Y/%m/%d")
    return {
        "solids": {
            "rollup_data": {
                "inputs": {"data_path": {"value": "s3://bucket-name/data/{}".format(date_path)}}
            }
        },
    }


@schedule(
    name="test_schedule", cron_schedule="* * * * *", pipeline_name="metrics_pipeline",
)
def test_schedule(_):
    return {
        "solids": {
            "save_metrics": {
                "inputs": {"data_path": {"value": "s3://bucket-name/data/{}".format("date")}}
            }
        },
    }


def define_schedules():
    return [daily_ingest_schedule, daily_rollup_schedule, test_schedule]


@solid
def save_metrics(context, data_path):
    context.log.info("Saving metrics to path {data_path}".format(data_path=data_path))


@pipeline(
    preset_defs=[
        PresetDefinition(
            name="test",
            run_config={
                "solids": {
                    "save_metrics": {
                        "inputs": {"data_path": {"value": "s3://bucket-name/test_data"}}
                    }
                }
            },
        ),
    ],
)
def metrics_pipeline():
    save_metrics()


@solid
def rollup_data(context, data_path):
    context.log.info("Rolling up data from path {data_path}".format(data_path=data_path))


@pipeline(
    preset_defs=[
        PresetDefinition(
            name="test",
            run_config={
                "solids": {
                    "rollup_data": {
                        "inputs": {"data_path": {"value": "s3://bucket-name/test_data"}}
                    }
                }
            },
        ),
    ],
)
def rollup_pipeline():
    rollup_data()


@solid
def test_solid(_):
    return 1


@pipeline
def test_pipeline():
    test_solid()


@repository
def experimental_repository():
    return [test_pipeline, metrics_pipeline, rollup_pipeline] + define_schedules()
