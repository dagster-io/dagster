# pylint: disable=unused-argument

import datetime

from dagster import In, RunRequest, job, op, repository, sensor
from dagster._legacy import daily_schedule


@op
def return_one():
    return 1


@op
def return_two():
    return 2


@op(ins={"left": In(), "right": In()})
def add(left, right):
    return left + right


@op(ins={"left": In(), "right": In()})
def subtract(left, right):
    return left - right


# start_lazy_repository_definition_marker_0
def load_addition_pipeline():
    @job
    def addition_job():
        return add(return_one(), return_two())

    return addition_job


def load_subtraction_pipeline():
    @job
    def subtraction_job():
        return subtract(return_one(), return_two())

    return subtraction_job


def load_daily_addition_schedule():
    @daily_schedule(
        pipeline_name="addition_job",
        start_date=datetime.datetime(2020, 1, 1),
    )
    def daily_addition_schedule(date):
        return {}

    return daily_addition_schedule


def load_addition_sensor():
    @sensor(job_name="addition_job")
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
            "addition_job": load_addition_pipeline,
            "subtraction_job": load_subtraction_pipeline,
        },
        "jobs": {"my_job": my_job},
        "schedules": {"daily_addition_schedule": load_daily_addition_schedule},
        "sensors": {"addition_sensor": load_addition_sensor},
    }


# end_lazy_repository_definition_marker_0
