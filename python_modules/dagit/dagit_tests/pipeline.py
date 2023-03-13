from dagster import In, Out, repository
from dagster._core.definitions.decorators import op
from dagster._core.test_utils import today_at_midnight
from dagster._legacy import daily_schedule, pipeline


@op(ins={"num": In(int)}, out=Out(int))
def add_one(num):
    return num + 1


@op(ins={"num": In(int)}, out=Out(int))
def mult_two(num):
    return num * 2


@pipeline
def math():
    return mult_two(num=add_one())


@daily_schedule(
    job_name="math",
    start_date=today_at_midnight(),
)
def my_schedule(_):
    return {"solids": {"mult_two": {"inputs": {"num": {"value": 2}}}}}


@repository
def test_repository():
    return [math]
