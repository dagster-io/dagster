from dagster import In, Int, Out, op, repository
from dagster._legacy import pipeline


@op(ins={"num": In(Int)}, out=Out(Int))
def add_one(num):
    return num + 1


@op(ins={"num": In(Int)}, out=Out(Int))
def mult_two(num):
    return num * 2


@pipeline
def math():
    return mult_two(num=add_one())


@repository
def test_override_repository():
    return [math]
