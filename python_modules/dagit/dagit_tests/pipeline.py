from dagster import In, Out, repository
from dagster._core.definitions.decorators import op
from dagster._core.definitions.decorators.schedule_decorator import schedule
from dagster._legacy import pipeline


@op(ins={"num": In(int)}, out=Out(int))
def add_one(num):
    return num + 1


@op(ins={"num": In(int)}, out=Out(int))
def mult_two(num):
    return num * 2


@pipeline
def math():
    return mult_two(num=add_one())


@schedule(
    cron_schedule="@daily",
    job_name="math",
)
def my_schedule(_):
    return {"ops": {"mult_two": {"inputs": {"num": {"value": 2}}}}}


@repository
def test_repository():
    return [math]
