# pylint: disable=unused-argument

import datetime

from dagster import InputDefinition, daily_schedule, lambda_solid, pipeline, repository


@lambda_solid
def return_one():
    return 1


@lambda_solid
def return_two():
    return 2


@lambda_solid(input_defs=[InputDefinition("left"), InputDefinition("right")])
def add(left, right):
    return left + right


@lambda_solid(input_defs=[InputDefinition("left"), InputDefinition("right")])
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


@repository
def my_repository():
    return [addition_pipeline, subtraction_pipeline, daily_addition_schedule]


# end_repository_definition_marker_0
