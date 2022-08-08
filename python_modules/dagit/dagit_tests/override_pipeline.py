from dagster import In, Out, op, Int, repository
from dagster._legacy import InputDefinition, OutputDefinition, lambda_solid, pipeline


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
