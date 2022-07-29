from dagster import Int, daily_schedule, repository
from dagster._core.test_utils import today_at_midnight
from dagster._legacy import InputDefinition, OutputDefinition, lambda_solid, pipeline


@lambda_solid(input_defs=[InputDefinition("num", Int)], output_def=OutputDefinition(Int))
def add_one(num):
    return num + 1


@lambda_solid(input_defs=[InputDefinition("num", Int)], output_def=OutputDefinition(Int))
def mult_two(num):
    return num * 2


@pipeline
def math():
    return mult_two(num=add_one())


@daily_schedule(
    pipeline_name="math",
    start_date=today_at_midnight(),
)
def my_schedule(_):
    return {"solids": {"mult_two": {"inputs": {"num": {"value": 2}}}}}


@repository
def test_repository():
    return [math]
