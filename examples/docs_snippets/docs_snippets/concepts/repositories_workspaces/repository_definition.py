# pylint: disable=unused-argument

import datetime

from dagster import InputDefinition, RunRequest, daily_schedule, pipeline, repository, sensor, solid


@solid
def return_one():
    return 1


@solid
def return_two():
    return 2


@solid(input_defs=[InputDefinition("left"), InputDefinition("right")])
def add(left, right):
    return left + right


@solid(input_defs=[InputDefinition("left"), InputDefinition("right")])
def subtract(left, right):
    return left - right


# start_repository_definition_marker_0
@pipeline
def addition_pipeline():
    return add(return_one(), return_two())


@pipeline
def subtraction_pipeline():
    return subtract(return_one(), return_two())


@daily_schedule(
    pipeline_name="addition_pipeline",
    start_date=datetime.datetime(2020, 1, 1),
)
def daily_addition_schedule(date):
    return {}


@sensor(pipeline_name="addition_pipeline")
def addition_sensor(context):
    should_run = True
    if should_run:
        yield RunRequest(run_key=None, run_config={})


@repository
def my_repository():
    return [
        addition_pipeline,
        subtraction_pipeline,
        daily_addition_schedule,
        addition_sensor,
    ]


# end_repository_definition_marker_0
