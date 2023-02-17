from dagster import In, Out, repository
from dagster._core.definitions.decorators import op
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


@repository
def test_override_repository():
    return [math]
