from dagster import job, In, Out, op, Int, repository
from dagster._core.test_utils import today_at_midnight
from dagster._legacy import (
    daily_schedule,
)


@op(ins={"num": In(Int)}, out=Out(Int))
def add_one(num):
    return num + 1


@op(ins={"num": In(Int)}, out=Out(Int))
def mult_two(num):
    return num * 2


@job
def math():
    mult_two(num=add_one())


@daily_schedule(
    pipeline_name="math",
    start_date=today_at_midnight(),
)
def my_schedule(_):
    return {"solids": {"mult_two": {"inputs": {"num": {"value": 2}}}}}


@repository
def test_repository():
    return [math]
