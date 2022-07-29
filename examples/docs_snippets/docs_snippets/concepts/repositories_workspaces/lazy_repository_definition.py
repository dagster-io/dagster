# pylint: disable=unused-argument

import datetime

from dagster import RunRequest, daily_schedule, job, repository, sensor
from dagster._legacy import InputDefinition, pipeline, solid


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


# start_lazy_repository_definition_marker_0
def load_addition_pipeline():
    @pipeline
    def addition_pipeline():
        return add(return_one(), return_two())

    return addition_pipeline


def load_subtraction_pipeline():
    @pipeline
    def subtraction_pipeline():
        return subtract(return_one(), return_two())

    return subtraction_pipeline


def load_daily_addition_schedule():
    @daily_schedule(
        pipeline_name="addition_pipeline",
        start_date=datetime.datetime(2020, 1, 1),
    )
    def daily_addition_schedule(date):
        return {}

    return daily_addition_schedule


def load_addition_sensor():
    @sensor(pipeline_name="addition_pipeline")
    def addition_sensor(context):
        should_run = True
        if should_run:
            yield RunRequest(run_key=None, run_config={})

    return addition_sensor


@job
def my_job():
    return_one()


@repository
def my_lazy_repository():
    # Note that we can pass a dict of functions, rather than a list of
    # pipeline definitions. This allows us to construct pipelines lazily,
    # if, e.g., initializing a pipeline involves any heavy compute
    return {
        "pipelines": {
            "addition_pipeline": load_addition_pipeline,
            "subtraction_pipeline": load_subtraction_pipeline,
        },
        "jobs": {"my_job": my_job},
        "schedules": {"daily_addition_schedule": load_daily_addition_schedule},
        "sensors": {"addition_sensor": load_addition_sensor},
    }


# end_lazy_repository_definition_marker_0
